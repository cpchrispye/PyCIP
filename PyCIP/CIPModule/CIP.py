import threading
import queue
import time
from DataTypesModule.CPF import CPF_Codes
import struct
from DataTypesModule.DataTypes import *
from DataTypesModule.DataParsers import *
from DataTypesModule.signaling import Signaler, SignalerM2M
from collections import OrderedDict as O_Dict
from CIPModule.connection_manager_class import ConnectionManager

class Basic_CIP():

    def __init__(self, transportLayer, **kwargs):
        self.trans = transportLayer
        self.sequence_number = 1
        self.connected = False
        self.OT_connection_id = None
        self.TO_connection_id = None
        self.active = True
        self.transport_messenger = Signaler()
        self.cip_messenger = SignalerM2M()
        self._cip_manager_thread = threading.Thread(target=self._CIP_manager, args=[self.trans])
        self._cip_manager_thread.start()

    def _CIP_manager(self, trans):
        while self.active:
            message_structure = self.transport_messenger.get_message()
            packet = message_structure.message

            signal_id = 0
            # UnConnected Explicit
            if (packet.CPF[0].Type_ID == CPF_Codes.NullAddress
            and packet.CPF[1].Type_ID == CPF_Codes.UnconnectedData):
                message_response = MessageRouterResponseStruct_UCMM()
                message_response.import_data(packet.data)
                packet.CIP = message_response
                packet.data = packet.data[packet.CIP.byte_size:]
                signal_id = packet.encapsulation_header.Sender_Context
                self.transport_messenger.unregister(message_structure.signal_id)

            # Connected Explicit
            elif(packet.CPF[0].Type_ID == CPF_Codes.ConnectedAddress
            and packet.CPF[1].Type_ID == CPF_Codes.ConnectedData):
                message_response = MessageRouterResponseStruct()
                message_response.import_data(packet.data)
                packet.CIP = message_response
                packet.data = packet.data[packet.CIP.byte_size:]
                signal_id = message_response.Sequence_Count

            # Connected Implicit
            elif(packet.CPF[0].Type_ID == CPF_Codes.SequencedAddress
            and packet.CPF[1].Type_ID == CPF_Codes.ConnectedData):
                print("Connected Implicit Not Supported Yet")
                continue
            self.cip_messenger.send_message(signal_id, packet)

    def get_next_sender_context(self):
        return self.trans.get_next_sender_context()

    def set_connection(self, OT_connection_id, TO_connection_id):
        self.connected = True
        self.OT_connection_id = OT_connection_id
        self.TO_connection_id = TO_connection_id

    def clear_connection(self):
        self.connected = False
        self.OT_connection_id = None
        self.TO_connection_id = None

    def explicit_message(self, service, *EPath, data=bytes(), receive=True):
        packet = bytearray()
        if self.connected:
            self.sequence_number += 1
            sequence_number = self.sequence_number
            packet += struct.pack('H', sequence_number)

        packet.append(service)
        EPath_bytes = bytes()
        for item in EPath:
            EPath_bytes += item
        packet.append(len(EPath_bytes)//2)
        packet += EPath_bytes
        packet += data

        if receive:
            receive_id = self.TO_connection_id if self.TO_connection_id else self.trans.get_next_sender_context()
            # if we want the manager to be notified that this message has been responded too, we must register
            self.transport_messenger.register(receive_id)
            if self.connected:
                receipt =  sequence_number
            else:
                receipt =  receive_id
            self.cip_messenger.register(receipt)
        else:
            receive_id = None

        # SEND PACKET
        context = self.trans.send_encap(packet, self.OT_connection_id, receive_id)

        return receipt

    def receive(self, receive_id, time_out=5):
        return self.cip_messenger.get_message(receive_id, time_out).message

    def get_attr_single(self, class_int, instance_int, attribute_int):

        class_val = EPath_item(SegmentType.LogicalSegment, LogicalType.ClassID, LogicalFormat.bit_8, class_int)
        insta_val = EPath_item(SegmentType.LogicalSegment, LogicalType.InstanceID, LogicalFormat.bit_8, instance_int)
        attri_val = EPath_item(SegmentType.LogicalSegment, LogicalType.AttributeID, LogicalFormat.bit_8, attribute_int)

        receipt = self.explicit_message(CIPServiceCode.get_att_single, class_val, insta_val, attri_val)
        return self.receive(receipt)

    def get_attr_all(self, class_int, instance_int):

        class_val = EPath_item(SegmentType.LogicalSegment, LogicalType.ClassID, LogicalFormat.bit_8, class_int)
        insta_val = EPath_item(SegmentType.LogicalSegment, LogicalType.InstanceID, LogicalFormat.bit_8, instance_int)

        receipt = self.explicit_message(CIPServiceCode.get_att_all, class_val, insta_val)
        return self.receive(receipt)

    def set_attr_single(self, class_int, instance_int, attribute_int, data):

        class_val = EPath_item(SegmentType.LogicalSegment, LogicalType.ClassID, LogicalFormat.bit_8, class_int)
        insta_val = EPath_item(SegmentType.LogicalSegment, LogicalType.InstanceID, LogicalFormat.bit_8, instance_int)
        attri_val = EPath_item(SegmentType.LogicalSegment, LogicalType.AttributeID, LogicalFormat.bit_8, attribute_int)

        receipt = self.explicit_message(CIPServiceCode.set_att_single, class_val, insta_val, attri_val, data=data)
        return self.receive(receipt)

#vol1 ver 3.18 2-4.2
class MessageRouterResponseStruct(CIPDataStructure):
    global_structure = OrderedDict((('Sequence_Count', 'UINT'),
                                     ('Reply_Service', 'USINT'),
                                     ('Reserved', 'USINT'),
                                     ('General_Status', 'USINT'),
                                     ('Size_of_Additional_Status', 'USINT'),
                                     ('Additional_Status', ['Size_of_Additional_Status', 'WORD']))
                                    )
#vol1 ver 3.18 2-4.2
class MessageRouterResponseStruct_UCMM(CIPDataStructure):
    global_structure = OrderedDict((('Reply_Service', 'USINT'),
                                     ('Reserved', 'USINT'),
                                     ('General_Status', 'USINT'),
                                     ('Size_of_Additional_Status', 'USINT'),
                                     ('Additional_Status', ['Size_of_Additional_Status', 'WORD'])
                                     ))


class CIP_Manager():

    def __init__(self, trasport, *EPath):
        pass
