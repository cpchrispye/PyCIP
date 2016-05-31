from enum import IntEnum
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

class SegType():
    pass

class PortSegment(SegType):

    def __init__(self, port=None, link_address=None, bytes_object=None):
        self.port = port
        self.link_address = link_address
        self.link_address_size = 1
        self.extended_port = False
        self.bytes_object = bytes_object

        if port != None and link_address != None:
            self.bytes_object = self.build(port, link_address)

    def build(self, port, link_address):
        temp_byte = 0
        data_out = bytearray()
        if hasattr(link_address, '__len__') and len(link_address) > 1:
            temp_byte |= 1 << 4
            data_out.append(len(link_address))
            self.link_address_size = len(link_address)
        if port >= 15:
            temp_byte |= 0x0f
            data_out += struct.pack('H', port)
            self.extended_port = True
        temp_byte |= 0x07 & port
        data_out.insert(0, temp_byte)
        if not isinstance(link_address, (list, tuple)):
            link_address = [link_address]
        data_out += bytes(link_address)
        if len(data_out) % 2:
            data_out += bytearray(0)
        return data_out

    def export_data(self):
        return self.build(self.port, self.link_address)

    def import_data(self, data):
        self.bytes_object = data

    def __str__(self):
        if self.port != None and self.link_address != None:
            return "PortSegment: Port %s, Link %s, Extended %s, Address size %s" % (self.port, self.link_address,
                                                                                    self.extended_port, self.link_address_size)
        return "PortSegment NULL"

class LogicalSegment(SegType):

    def __init__(self, logical_type=None, format=None, value=None, bytes_object=None):
        self.logical_type = logical_type
        self.format = format
        self.value = value
        self.bytes_object = bytes_object

        if self.logical_type != None and self.format != None and self.value != None:
            self.bytes_object = self.build(self.logical_type, self.format, self.value)

    def build(self, logical_type, format, value):
        temp_byte = 0x07 & SegmentType.LogicalSegment
        temp_byte = temp_byte << 3
        temp_byte |= 0x07 & logical_type
        temp_byte = temp_byte << 2
        temp_byte |= 0x03 & format
        data_out = struct.pack('B', temp_byte)
        data_out = data_out + struct.pack('B', value)
        return data_out

    def export_data(self):
        return self.build(self.logical_type, self.format, self.value)

    def import_data(self, data):
        self.bytes_object = data

    def __str__(self):
        if self.logical_type != None and self.format != None and self.value != None:
            return "Logical: Type %s, format %s, value %s" % (str(LogicalType(self.logical_type)).split('.')[1],
                                                              str(LogicalFormat(self.format)).split('.')[1],
                                                              self.value)
        return "LogicalSegment NULL"

class EPATH(list):

    def add(self, EPATH_type):
        self.append(EPATH_type)




class BaseDataParser():
    @staticmethod
    def _parse(data, byte_size, signed, offset=0):
        section = data[offset: offset + byte_size]
        return int.from_bytes(section, 'little', signed=signed )

    @staticmethod
    def _build(value, byte_size, signed):
        return value.to_bytes(byte_size, 'little', signed=signed)

    def import_data(self, data, offset=0):
        return self._parse(data, self.byte_size, self.signed, offset)

    def export_data(self, value):
        return self._build(value, self.byte_size, self.signed)

class Array_CIP(BaseDataParser):

    def __init__(self, data_type, size=None):
        self.data_type = data_type
        self.size = size

    def import_data(self, data, offset=0):
        i=0

class StringDataParser():

    def __init__(self, char_size=1):
        self.char_size = char_size
        self.byte_size = 0

    def import_data(self, data, offset=0):
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

    def import_data(self, data, offset=0):
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


CIPDataTypes = {
    "octet": BYTE_CIP(),
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