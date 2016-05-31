from collections import OrderedDict
import random
from DataTypesModule.DataParsers import *
from DataTypesModule.DataTypes import *

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

        self.struct_fwd_open_rsp = CIPDataStructure(
                                                        ('OT_connection_ID', 'UDINT'),
                                                        ('TO_connection_ID', 'UDINT'),
                                                        ('connection_serial', 'UINT'),
                                                        ('O_vendor_ID', 'UINT'),
                                                        ('O_serial', 'UDINT'),
                                                        ('OT_API', 'UDINT'),
                                                        ('TO_API', 'UDINT'),
                                                        ('Application_Size', 'USINT'),
                                                        ('Reserved', 'USINT'),
                                                        ('Data', ['Application_Size', 'BYTE']),
                                                    )

        self.struct_fwd_open_send = CIPDataStructure(
                                                        ('tick','BYTE'),
                                                        ('time_out','USINT'),
                                                        ('OT_connection_ID','UDINT'),
                                                        ('TO_connection_ID','UDINT'),
                                                        ('connection_serial','UINT'),
                                                        ('O_vendor_ID','UINT'),
                                                        ('O_serial','UDINT'),
                                                        ('time_out_multiplier','USINT'),
                                                        ('reserved_1','octet'),
                                                        ('reserved_2','octet'),
                                                        ('reserved_3','octet'),
                                                        ('OT_RPI','UDINT'),
                                                        ('OT_connection_params','WORD'),
                                                        ('TO_RPI','UDINT'),
                                                        ('TO_connection_params','WORD'),
                                                        ('trigger','BYTE'),
                                                        ('path_len','USINT')
                                                    )

    def unconnected_send(self, data, route):

        packet = bytearray()
        class_val = EPath_item(SegmentType.LogicalSegment, LogicalType.ClassID, LogicalFormat.bit_8, 6)
        insta_val = EPath_item(SegmentType.LogicalSegment, LogicalType.InstanceID, LogicalFormat.bit_8, 1)

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

        receipt = self.trans.explicit_message(CIPServiceCode.unconnected_Send, class_val, insta_val, data=packet, use_UCMM=False)
        #response = self.trans.receive(receipt)
        return receipt


    def forward_open(self, EPath, **kwargs):

        message_router_path = EPATH()
        message_router_path.append(LogicalSegment(LogicalType.ClassID, LogicalFormat.bit_8, 6))
        message_router_path.append(LogicalSegment(LogicalType.InstanceID, LogicalFormat.bit_8, 1))

        connection_path_bytes = EPath.export_data()

        # build default fwd open parameters
        self.struct_fwd_open_send.tick = 6
        self.struct_fwd_open_send.time_out = 0x28
        self.struct_fwd_open_send.OT_connection_ID = random.randrange(1, 99999)
        self.struct_fwd_open_send.TO_connection_ID = self.trans.get_next_sender_context()
        self.struct_fwd_open_send.connection_serial = random.randrange(0, 2^16)
        self.struct_fwd_open_send.O_vendor_ID = 88
        self.struct_fwd_open_send.O_serial = 12345678
        self.struct_fwd_open_send.time_out_multiplier = 0
        self.struct_fwd_open_send.reserved_1 = 0
        self.struct_fwd_open_send.reserved_2 = 0
        self.struct_fwd_open_send.reserved_3 = 0
        self.struct_fwd_open_send.OT_RPI = 0x03E7FC18
        self.struct_fwd_open_send.OT_connection_params = 0x43FF
        self.struct_fwd_open_send.TO_RPI = 0x03E7FC18
        self.struct_fwd_open_send.TO_connection_params = 0x43FF
        self.struct_fwd_open_send.trigger = 0xa3
        self.struct_fwd_open_send.path_len = len(connection_path_bytes)//2

        # update parameters
        for key in self.struct_fwd_open_send.keys():
            if key in kwargs:
                self.struct_fwd_open_send[key] = kwargs[key]

        command_specific = self.struct_fwd_open_send.export_data()

        receipt = self.trans.explicit_message(CIPServiceCode.forward_open, message_router_path, data=(command_specific + connection_path_bytes))
        response = self.trans.receive(receipt)
        if response and response.CIP.General_Status == 0:
            self.struct_fwd_open_rsp.import_data(response.data)
            return self.struct_fwd_open_rsp
        return None