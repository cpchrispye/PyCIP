from enum import IntEnum
import struct


class TransportPacket():

    def __init__(self, transport_meta_data=None, encapsulation_header=None, command_specific=None, CPF=None, data=None, CIP=None):
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
    forward_open   = 0x54

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

def EPath_item(*args):
    seg_type = args[0]
    data_out = 0
    if  seg_type == SegmentType.PortSegment:
        pass
    elif seg_type == SegmentType.LogicalSegment:
        data_out = 0x07 & args[0]
        data_out = data_out << 3
        data_out |= 0x07 & args[1]
        data_out = data_out << 2
        data_out |= 0x03 & args[2]
        data_out = struct.pack('B', data_out)
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


class BaseDataParser():
    @staticmethod
    def _parse(data, byte_size, signed, offset=0):
        section = data[offset: offset + byte_size]
        return int.from_bytes(section, 'little', signed=signed )

    @staticmethod
    def _build(value, byte_size, signed):
        return value.to_bytes(byte_size, 'little', signed=signed)

    def parse(self, data, offset=0):
        return self._parse(data, self.byte_size, self.signed, offset)

    def build(self, value):
        return self._build(value, self.byte_size, self.signed)

class Array_CIP(BaseDataParser):

    def __init__(self, data_type, size=None):
        self.data_type = data_type
        self.size = size

    def parse(self, data, offset=0):
        i=0

class StringDataParser():

    def __init__(self, char_size=1):
        self.char_size = char_size
        self.byte_size = 0

    def parse(self, data, offset=0):
        section = data[offset: offset + 2]
        offset += 2
        string_size =  int.from_bytes(section, 'little', signed=0 )
        section = data[offset: offset + (self.char_size * string_size)]

        self.byte_size = offset + (self.char_size * string_size)

        if self.char_size == 1:
            return section.decode('iso-8859-1').encode('utf-8')
        elif self.char_size > 1:
            return bytes.decode('utf-8').encode('utf-8')
        else:
            return u'Error: Incorrect character size defined'

class ShortStringDataParser():

    def __init__(self):
        self.char_size = 1

    def parse(self, data, offset=0):
        section = data[offset: offset + 1]
        offset += 1
        string_size =  int.from_bytes(section, 'little', signed=0 )
        section = data[offset: offset + (self.char_size * string_size)]
        self.byte_size = offset + (self.char_size * string_size)

        string_parsed = section.decode('iso-8859-1')
        utf_encoded = string_parsed.encode('utf-8')
        return utf_encoded

class BOOL_CIP(BaseDataParser):
    byte_size = 1
    signed = 0

class SINT_CIP(BaseDataParser):
    byte_size = 1
    signed = 1

class INT_CIP(BaseDataParser):
    byte_size = 2
    signed = 1

class DINT_CIP(BaseDataParser):
    byte_size = 4
    signed = 1

class LINT_CIP(BaseDataParser):
    byte_size = 8
    signed = 1

class USINT_CIP(BaseDataParser):
    byte_size = 1
    signed = 0

class UINT_CIP(BaseDataParser):
    byte_size = 2
    signed = 0

class UDINT_CIP(BaseDataParser):
    byte_size = 4
    signed = 0

class ULINT_CIP(BaseDataParser):
    byte_size = 8
    signed = 0

class BYTE_CIP(BaseDataParser):
    byte_size = 1
    signed = 0

class WORD_CIP(BaseDataParser):
    byte_size = 2
    signed = 0

class DWORD_CIP(BaseDataParser):
    byte_size = 4
    signed = 0

class LWORD_CIP(BaseDataParser):
    byte_size = 8
    signed = 0

class EPATH(BaseDataParser):
    def parse(self, data, offset=0):
        print("Encounted EPATH Fail!!")
        return 0

CIPDataTypes = {
    "BOOL" : BOOL_CIP(),
    "SINT" : SINT_CIP(),
    "INT"  : INT_CIP(),
    "DINT" : DINT_CIP(),
    "LINT" : LINT_CIP(),
    "USINT": USINT_CIP(),
    "UINT" : UINT_CIP(),
    "UDINT": UDINT_CIP(),
    "ULINT": ULINT_CIP(),
    "BYTE" : BYTE_CIP(),
    "WORD" : WORD_CIP(),
    "DWORD": DWORD_CIP(),
    "LWORD": LWORD_CIP(),
    "SHORT_STRING" : ShortStringDataParser(),
    "STRING" : StringDataParser(1),
    "STRING2": StringDataParser(2),
    "EPATH": EPATH()
}