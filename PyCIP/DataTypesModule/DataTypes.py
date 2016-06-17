from enum import IntEnum
from collections import OrderedDict
import struct

class TransportPacket():

    def __init__(self, transport_meta_data=None, encapsulation_header=None, command_specific=None, CPF=None, data=None, CIP=None):
        self.response_id = None
        self.transport_meta_data = transport_meta_data
        self.encapsulation_header = encapsulation_header
        self.command_specific = command_specific
        self.CPF = CPF
        self.CIP = CIP
        self.offset = 0
        self.data = data

    def show_data_hex(self):
        return ' '.join(format(x, '02x') for x in self.data)

class CIPServiceCode(IntEnum):

    get_att_single = 0x0e
    set_att_single = 0x10
    get_att_all    = 0x01
    set_att_all    = 0x02
    unconnected_Send = 0x52
    forward_open   = 0x54
    forward_close  = 0x4E

class SegmentType(IntEnum):

    PortSegment     = 0
    LogicalSegment  = 1
    NetworkSegment  = 2
    SymbolicSegment = 3
    DataSegment     = 4
    DataType_c      = 5
    DataType_e      = 6
    Reserved        = 7

class LogicalType(IntEnum):

    ClassID         = 0
    InstanceID      = 1
    MemberID        = 2
    ConnectionPoint = 3
    AttributeID     = 4
    Special         = 5
    ServiceID       = 6
    ExtendedLogical = 7

class LogicalFormat(IntEnum):

    bit_8    = 0
    bit_16   = 1
    bit_32   = 2
    Reserved = 3

class DataSubType(IntEnum):

    SimpleData = 0
    ANSI       = 9

# depreciated
def EPath_item(*args, **kwargs):
    seg_type = args[0]
    temp_byte = 0
    data_out = bytearray()
    if  seg_type == SegmentType.PortSegment:
        port = args[1]
        link_address = args[2] # can be a list or a int
        if hasattr(link_address, '__len__') and len(link_address) > 1:
            temp_byte |= 1 << 4
            data_out.append(len(link_address))

        if port >= 15:
            temp_byte |= 0x0f
            data_out += struct.pack('H', port)
        temp_byte |= 0x07 & port
        data_out.insert(0, temp_byte)
        if not isinstance(link_address, (list, tuple)):
            link_address = [link_address]
        data_out += bytes(link_address)
        if len(data_out) % 2:
            data_out += bytearray(0)

    elif seg_type == SegmentType.LogicalSegment:
        temp_byte = 0x07 & args[0]
        temp_byte = temp_byte << 3
        temp_byte |= 0x07 & args[1]
        temp_byte = temp_byte << 2
        temp_byte |= 0x03 & args[2]
        data_out = struct.pack('B', temp_byte)
        data_out = data_out + struct.pack('B', args[3])

    elif seg_type == SegmentType.NetworkSegment:
        pass
    elif seg_type == SegmentType.DataSegment:
        pass
    elif seg_type == SegmentType.DataType_c:
        pass
    elif seg_type == SegmentType.DataType_e:
        pass
    elif seg_type == SegmentType.Reserved:
        pass
    return data_out
