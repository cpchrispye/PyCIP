from threading import Thread
#from multiprocessing import Process as Thread
from enum import IntEnum
from CIPModule.connection_manager_class import ConnectionManager, Trigger
from DataTypesModule import *
from collections import OrderedDict
from Tools.signaling import Signaler, SignalerM2M
import struct


class Basic_CIP():

    def __init__(self, transportLayer, **kwargs):
        self.trans = transportLayer
        self.sequence_number = 1
        self.connected = False
        self.OT_connection_id = None
        self.TO_connection_id = None
        self.active = True
        self._IO_input_data = bytes()
        self.transport_messenger = Signaler()
        self.cip_messenger = SignalerM2M()
        self._cip_manager_thread = Thread(target=self._CIP_manager, args=[self.trans], name="cip_layer")
        self._cip_manager_thread.start()

    def _CIP_manager(self, trans):
        while self.active and self.trans.connected:
            message_structure = self.transport_messenger.get_message(0.1)
            if message_structure == None:
                continue
            packet = message_structure.message

            signal_id = 0
            # UnConnected Explicit
            if (packet.CPF[0].Type_ID == CPF_Codes.NullAddress
            and packet.CPF[1].Type_ID == CPF_Codes.UnconnectedData):
                data = packet.CIP
                packet.CIP = MessageRouterResponseStruct_UCMM()
                packet.CIP.import_data(data)
                signal_id = packet.Encapsulation_header.Sender_Context
                self.transport_messenger.unregister(message_structure.signal_id)

            # Connected Explicit
            elif(packet.CPF[0].Type_ID == CPF_Codes.ConnectedAddress
            and packet.CPF[1].Type_ID == CPF_Codes.ConnectedData):
                packet.data = packet.CPF[1].data
                message_response = MessageRouterResponseStruct()
                message_response.import_data(packet.data)
                packet.CIP = message_response
                packet.data = packet.data[packet.CIP.sizeof():]
                signal_id = message_response.Sequence_Count

            # Connected Implicit
            elif(packet.CPF[0].Type_ID == CPF_Codes.SequencedAddress
            and packet.CPF[1].Type_ID == CPF_Codes.ConnectedData):
                if self.trigger.Transport_Class() == 0:
                    packet.CIP = IO_Response_0_Struct(packet.CIP)
                elif self.trigger.Transport_Class() == 1:
                    packet.CIP = IO_Response_1_Struct(packet.CIP)
                self._set_IO_Receive(packet.Response_Data)
                continue
            self.cip_messenger.send_message(signal_id, packet)

        return None
    def get_next_sender_context(self):
        return self.trans.get_next_sender_context()

    def set_connection(self, trigger, OT_connection_id, TO_connection_id, source_port=None, dest_port=None):
        self.connected = True
        self.trigger = Trigger(int(trigger))
        self.OT_connection_id = int(OT_connection_id)
        self.TO_connection_id = int(TO_connection_id)

        self.transport_messenger.register(self.TO_connection_id)
        if self.trigger.Transport_Class() <= 2:
            self.trans.connect_class_0_1(source_port=source_port, dest_port=dest_port)
        elif self.trigger.Transport_Class() <= 3:
            self.trans.connect_class_2_3()


    def clear_connection(self):
        self.connected = False
        self.OT_connection_id = None
        self.TO_connection_id = None

    def explicit_message(self, service, EPath, data=None, receive=True):
        packet = bytearray()
        if self.connected:
            self.sequence_number += 1
            sequence_number = self.sequence_number
            packet += struct.pack('H', sequence_number)

        packet += explicit_request(service, EPath, data=data)

        if receive:
            receive_id = self.TO_connection_id if self.TO_connection_id else self.trans.get_next_sender_context()
            # if we want the manager to be notified that this message has been responded too, we must register
            self.transport_messenger.register(receive_id)
            if self.connected:
                receipt = sequence_number
            else:
                receipt = receive_id
            self.cip_messenger.register(receipt)
        else:
            receive_id = None

        # SEND PACKET
        context = self.trans.send_encap(packet, self.OT_connection_id, receive_id)

        return receipt

    def receive(self, receive_id, time_out=5):
        message = self.cip_messenger.get_message(receive_id, time_out)
        if message:
            return message.message
        else:
            return None

    def IO_Receive(self):
        return self._IO_input_data

    def _set_IO_Receive(self, val):
        self._IO_input_data = val

class ReplyService(BaseBitFieldStruct):
    def __init__(self):
        self.RequestResponse = BaseBitField(1)
        self.Service = BaseBitField(7)

#vol1 ver 3.18 2-4.2
class MessageRouterResponseStruct(BaseStructureAutoKeys):

    def __init__(self, data=None):
        self.Sequence_Count = UINT()
        self.Reply_Service = ReplyService()
        self.Reserved = USINT()
        self.General_Status = USINT()
        self.Size_of_Additional_Status = USINT()
        self.Additional_Status = ARRAY(WORD, self.Size_of_Additional_Status)
        self.Response_Data = BYTES_RAW()

        if data is not None:
            self.import_data(data)

#vol1 ver 3.18 2-4.2
class MessageRouterResponseStruct_UCMM(BaseStructureAutoKeys):

    def __init__(self, data=None):
        self.Reply_Service = ReplyService()
        self.Reserved = USINT()
        self.General_Status = USINT()
        self.Size_of_Additional_Status = USINT()
        self.Additional_Status = ARRAY(WORD, self.Size_of_Additional_Status)
        self.Response_Data = BYTES_RAW()

        if data is not None:
            self.import_data(data)

class IO_Response_0_Struct(BaseStructureAutoKeys):

    def __init__(self, data=None):
        self.Response_Data = BYTES_RAW()

        if data is not None:
            self.import_data(data)

class IO_Response_1_Struct(BaseStructureAutoKeys):

    def __init__(self, data=None):
        self.Sequence_Count = UINT()
        self.Response_Data = BYTES_RAW()

        if data is not None:
            self.import_data(data)

def explicit_request(service, EPath, data=None):
    request = bytearray()
    request.append(service)
    EPath_bytes = EPath.export_data()
    request.append(len(EPath_bytes)//2)
    request += EPath_bytes
    if data is not None:
        request += data
    return request


class CIP_Manager():

    def __init__(self, transport, *EPath):
        self.trans = transport
        self.path = EPath
        self.primary_connection = Basic_CIP(transport)
        self.current_connection = self.primary_connection
        self.connection_manager = ConnectionManager(self.primary_connection)
        self.e_connected_connection = None

        # if there is a path then we make a connection
        if len(self.path):
            self.forward_open(*EPath)

    def forward_open(self, EPath=None, trigger=0xa3, **kwargs):
        if EPath == None:
            self.path = EPATH()
            self.path.append(LogicalSegment(LogicalType.ClassID, LogicalFormat.bit_8, 2))
            self.path.append(LogicalSegment(LogicalType.InstanceID, LogicalFormat.bit_8, 1))
        else:
            self.path = EPath
        fwd_rsp = self.connection_manager.forward_open(self.path, trigger=trigger,**kwargs)
        cp = Trigger(trigger)
        if fwd_rsp.CIP.General_Status == 0:
            self.e_connected_connection = Basic_CIP(self.trans)
            self.e_connected_connection.set_connection(trigger,
                                                       fwd_rsp.Response_Data.OT_connection_ID, fwd_rsp.Response_Data.TO_connection_ID, 2222, 2222)
            self.current_connection = self.e_connected_connection
            self._fwd_rsp = fwd_rsp.Response_Data
            return self._fwd_rsp
        return False

    def forward_close(self, EPath=None, **kwargs):
        if EPath == None:
            self.path = EPATH()
            self.path.append(LogicalSegment(LogicalType.ClassID, LogicalFormat.bit_8, 2))
            self.path.append(LogicalSegment(LogicalType.InstanceID, LogicalFormat.bit_8, 1))
        else:
            self.path = EPath
        fwd_rsp = self.connection_manager.forward_close(self.path, **kwargs)
        if fwd_rsp:
            try:
                self.current_connection.clear_connection()
                del self.current_connection
            except AttributeError:
                pass
            return fwd_rsp
        return False

    def explicit_message(self, service, request_path, data=None, route=None, try_connected=True):

        if try_connected and self.e_connected_connection and self.e_connected_connection.connected:
            connection = self.e_connected_connection
            receipt = connection.explicit_message(service, request_path, data=data)
        elif route:
            message = explicit_request(service, request_path, data=data)
            connection = self.connection_manager
            receipt = connection.unconnected_send(message, route)
        else:
            connection = self.primary_connection
            receipt = connection.explicit_message(service, request_path, data=data)

        return connection.receive(receipt)

    def get_attr_single(self, class_int, instance_int, attribute_int, try_connected=True, route=None):
        path = EPATH()
        path.append(LogicalSegment(LogicalType.ClassID, FormatSize(class_int), class_int))
        path.append(LogicalSegment(LogicalType.InstanceID, FormatSize(instance_int), instance_int))
        path.append(LogicalSegment(LogicalType.AttributeID, FormatSize(attribute_int), attribute_int))

        return self.explicit_message(CIPServiceCode.get_att_single, path, try_connected=try_connected, route=route)


    def get_attr_all(self, class_int, instance_int, try_connected=True, route=None):
        path = EPATH()
        path.append(LogicalSegment(LogicalType.ClassID, FormatSize(class_int), class_int))
        path.append(LogicalSegment(LogicalType.InstanceID, FormatSize(instance_int), instance_int))

        return self.explicit_message(CIPServiceCode.get_att_all, path, try_connected=try_connected, route=route)

    def set_attr_single(self, class_int, instance_int, attribute_int, data, try_connected=True, route=None):
        path = EPATH()
        path.append(LogicalSegment(LogicalType.ClassID, FormatSize(class_int), class_int))
        path.append(LogicalSegment(LogicalType.InstanceID, FormatSize(instance_int), instance_int))
        path.append(LogicalSegment(LogicalType.AttributeID, FormatSize(attribute_int), attribute_int))

        return self.explicit_message(CIPServiceCode.set_att_single, path, try_connected=try_connected, route=route)

    def set_attr_all(self, class_int, instance_int, data, try_connected=True, route=None):
        path = EPATH()
        path.append(LogicalSegment(LogicalType.ClassID, FormatSize(class_int), class_int))
        path.append(LogicalSegment(LogicalType.InstanceID, FormatSize(instance_int), instance_int))

        return self.explicit_message(CIPServiceCode.set_att_single, path, try_connected=try_connected, route=route)

    def read_input(self):
        return self.current_connection.IO_Receive()


class RoutingType(IntEnum):

    ExplicitDefault     = 0,
    ExplicitDirect      = 1,
    ExplicitConnected   = 2,
    ExplicitUnConnected = 3,

    ImplicitDefault     = 4,
    ImplicitDirect      = 5,
    ImplicitConnected   = 6,
    ImplicitUnConnected = 7,