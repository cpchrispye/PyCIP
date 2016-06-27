from collections import OrderedDict
import random
from DataTypesModule import *

class ConnectionParams(BaseBitFieldStruct):

    def __init__(self, value=None):
        self.Redundant_Owner = BaseBitField(1)
        self.Connection_Type = BaseBitField(2)
        self.Reserved = BaseBitField(1)
        self.Priority = BaseBitField(2)
        self.FixedVariable = BaseBitField(1)
        self.Connection_Size = BaseBitField(9)

        if value is not None:
            self(value)

class Trigger(BaseBitFieldStruct):

    def __init__(self, value=None):
        self.Direction = BaseBitField(1)
        self.Production_Trigger = BaseBitField(3)
        self.Transport_Class = BaseBitField(4)

        if value is not None:
            self.import_data(value.to_bytes(self.sizeof(), 'little'))


class Foward_Open_Send(BaseStructureAutoKeys):

    def __init__(self):
        self.tick                 = BYTE()
        self.time_out             = USINT()
        self.OT_connection_ID     = UDINT()
        self.TO_connection_ID     = UDINT()
        self.connection_serial    = UINT()
        self.O_vendor_ID          = UINT()
        self.O_serial             = UDINT()
        self.time_out_multiplier  = USINT()
        self.reserved             = ARRAY(BYTE, 3, 0)
        self.OT_RPI               = UDINT()
        self.OT_connection_params = ConnectionParams()
        self.TO_RPI               = UDINT()
        self.TO_connection_params = ConnectionParams()
        self.trigger              = Trigger()
        self.Connection_Path_Size = USINT()
        self.Connection_Path      = EPATH(self.Connection_Path_Size)

class Foward_Open_RSP(BaseStructureAutoKeys):

    def __init__(self):
        self.OT_connection_ID     = UDINT()
        self.TO_connection_ID     = UDINT()
        self.connection_serial    = UINT()
        self.O_vendor_ID          = UINT()
        self.O_serial             = UDINT()
        self.OT_API               = UDINT()
        self.TO_API               = UDINT()
        self.Application_Reply_Size = USINT()
        self.reserved               = ARRAY(BYTE, 3, 0)
        self.Application_Reply      = ARRAY(UINT, self.Application_Reply_Size)


class ConnectionManager():

    def __init__(self, transport, **kwargs):
        self.trans = transport

        #vol 1 3.18 3-5.4
        self.unconnected_send_struct_header = CIPDataStructure(
                                                                ('Time_tick', 'BYTE'),
                                                                ('Time_out_ticks', 'USINT'),
                                                                ('Embedded_Message_Request_Size', 'UINT'),
                                                               )
        self.unconnected_send_struct_footer = CIPDataStructure(
                                                                ('Route_Path_Size', 'USINT'),
                                                                ('Reserved', 'USINT'),
                                                               )



        self.struct_fwd_close_send = CIPDataStructure(
                                                        ('tick','BYTE'),
                                                        ('time_out','USINT'),
                                                        ('connection_serial','UINT'),
                                                        ('O_vendor_ID','UINT'),
                                                        ('O_serial','UDINT'),
                                                        ('Reserved', 'USINT'),
                                                        ('path_len','USINT')
                                                    )
    def unconnected_send(self, data, route):

        packet = bytearray()
        e_path = EPATH()
        e_path.append(LogicalSegment(LogicalType.ClassID, LogicalFormat.bit_8, 6))
        e_path.append(LogicalSegment( LogicalType.InstanceID, LogicalFormat.bit_8, 1))

        header = self.unconnected_send_struct_header
        header.Time_tick = 100
        header.Time_out_ticks = 100
        header.Embedded_Message_Request_Size = len(data)



        packet += header.export_data()
        packet += data
        if len(data) % 2:
            packet += bytes([0])

        footer = self.unconnected_send_struct_footer
        if hasattr(route, 'export_data'):
            port_path = route.export_data()
            footer.Route_Path_Size = route.byte_size // 2
            footer.Reserved = 0
        else:
            port_path = bytes()
            for item in route:
                port_path += item
            footer.Route_Path_Size = len(port_path)//2
            footer.Reserved = 0

        packet += footer.export_data()
        packet += port_path

        receipt = self.trans.explicit_message(CIPServiceCode.unconnected_Send, e_path, data=packet)
        return receipt


    def forward_open(self, EPath, tick=10, time_out=1, OT_connection_ID=None, TO_connection_ID=None, connection_serial=None,
                     O_vendor_ID=88, O_serial=12345678, time_out_multiplier=0, reserved_1=0, reserved_2=0, reserved_3=0, OT_RPI=0x03E7FC18,
                     OT_connection_params=0x43FF, TO_RPI=0x03E7FC18, TO_connection_params=0x43FF, trigger=0xa3):

        message_router_path = EPATH()
        message_router_path.append(LogicalSegment(LogicalType.ClassID, LogicalFormat.bit_8, 6))
        message_router_path.append(LogicalSegment(LogicalType.InstanceID, LogicalFormat.bit_8, 1))

        fwd_open = Foward_Open_Send()

        fwd_open.tick(tick)
        fwd_open.time_out(time_out)
        fwd_open.OT_connection_ID(OT_connection_ID if OT_connection_ID != None else random.randrange(1, 99999))
        fwd_open.TO_connection_ID(TO_connection_ID if TO_connection_ID != None else self.trans.get_next_sender_context())
        fwd_open.connection_serial(connection_serial if connection_serial != None else random.randrange(0, 2^16))
        fwd_open.O_vendor_ID(O_vendor_ID)
        fwd_open.O_serial(O_serial)
        fwd_open.time_out_multiplier(time_out_multiplier)
        fwd_open.OT_RPI(OT_RPI)
        fwd_open.OT_connection_params(OT_connection_params)
        fwd_open.TO_RPI(TO_RPI)
        fwd_open.TO_connection_params(TO_connection_params)
        fwd_open.trigger(trigger)
        fwd_open.Connection_Path_Size(EPath.sizeof()//2)
        fwd_open.Connection_Path = EPath

        receipt = self.trans.explicit_message(CIPServiceCode.forward_open, message_router_path, data=fwd_open.export_data())
        response = self.trans.receive(receipt)

        if response.CIP.General_Status == 0:
            rsp_data = response.Response_Data
            response.Response_Data = Foward_Open_RSP()
            response.Response_Data.import_data(rsp_data)

        if response is not None:
            return response
        return False



    def forward_close(self, EPath, tick=6, time_out=0x28, connection_serial=None, O_vendor_ID=88, O_serial=12345678):

        message_router_path = EPATH()
        message_router_path.append(LogicalSegment(LogicalType.ClassID, LogicalFormat.bit_8, 6))
        message_router_path.append(LogicalSegment(LogicalType.InstanceID, LogicalFormat.bit_8, 1))

        connection_path_bytes = EPath.export_data()

        self.struct_fwd_close_send.tick = tick
        self.struct_fwd_close_send.time_out = time_out
        self.struct_fwd_close_send.connection_serial = connection_serial if connection_serial != None else self.struct_fwd_open_send.connection_serial
        self.struct_fwd_close_send.O_vendor_ID = O_vendor_ID
        self.struct_fwd_close_send.O_serial = O_serial
        self.struct_fwd_close_send.Reserved = 0
        self.struct_fwd_close_send.path_len = len(connection_path_bytes)//2

        command_specific = self.struct_fwd_close_send.export_data()

        receipt = self.trans.explicit_message(CIPServiceCode.forward_close, message_router_path, data=(command_specific + connection_path_bytes))
        response = self.trans.receive(receipt)
        if response and response.CIP.General_Status == 0:
            self.struct_fwd_open_rsp.import_data(response.data)
            return self.struct_fwd_open_rsp
        return None
