from collections import OrderedDict
from  DataTypesModule import CIPServiceCode, SegmentType, LogicalType, LogicalFormat, DataSubType
import struct
import socket
import abc

class CIPDataStructureVirtual(object):
    __metaclass__ = abc.ABCMeta


    @abc.abstractmethod
    def keys(self):
        pass

    @abc.abstractmethod
    def import_data(self, bytes, offset=0):
        pass
    @abc.abstractmethod
    def export_data(self):
        pass

    def items(self):
        d = self.get_dict()
        return [(key, d[key]) for key in self.keys()]

    def get_dict(self):
        return {k:self.__dict__[k] for k in self.keys()}

    def __len__(self):
        return len(self.export_data())

    def pprint(self):
        string_list = []
        for key, val in self.items():
            try:
                tmp = ['\t' + x for x in val.pprint()]
                string_list.append("%s:-" % key)
                string_list += tmp
            except AttributeError:
                string_list.append("%s: %s" % (key, val))
        return string_list

    def print(self):
        return '\n'.join(self.pprint())

class CIPDataStructure(CIPDataStructureVirtual):
    global_structure = OrderedDict()

    def __init__(self, *data_tuple, **initial_values):
        self.structure = OrderedDict(self.global_structure)
        self.structure.update(data_tuple)
        self._keys = list(self.structure.keys())
        self._struct_list = tuple(self.structure.items())
        self.byte_size = 0
        self.data = {}
        self.set_values(initial_values)

    def __getattr__(self, item):
        if item in self.structure:
            return self.data[item]

    def __setattr__(self, key, value):
        if 'structure' in self.__dict__:
            if key in self.structure:
                self.data[key] = value
                return None
        super().__setattr__(key, value)

    def __getitem__(self, item):
        name = item
        if isinstance(item, int):
            name = self._keys[item]
        return self.data[name]

    def __setitem__(self, key, value):
        name = key
        if isinstance(key, int):
            name = self._keys[key]
        self.data[name] = value

    def __iter__(self):
        for key in self._keys:
            yield self.data[key]

    def set_values(self, dict_vals):
        for k, v in dict_vals.items():
            self.__setattr__(k, v)

    def items(self):
        return [(key, self.data[key]) for key in self._keys]

    def get_struct(self, index=None):
        if index:
            return self._struct_list[index]
        return self._struct_list

    def keys(self):
        return self._keys

    def import_data(self, bytes, offset=0):
        start_offset = offset
        for key, val in self.structure.items():
            try:
                # see if string representation of type is used
                if isinstance(val, str):
                    val = CIPDataTypes[val]
                # check to see if object need instantiating
                if val.__class__ == type:
                    val = val()
                # see if the type can parse
                self.data[key] = val.import_data(bytes, offset)
                offset += val.byte_size
            except (AttributeError, KeyError):
                sub_struct = val
                # otherwise if not a base unit type see if it is an array with length defined by a previous element
                if isinstance(val[0], str):
                    size = self.data[val[0]]
                    sub_struct = [(i, val[1]) for i in range(size)]
                 # otherwise if not a base unit type see if it is an array with length defined as int
                elif isinstance(val[0], int):
                    sub_struct = [(i, val[1]) for i in range(val[0])]
                # send new sub struct down as a new struct
                if isinstance(sub_struct, (list, tuple)):
                    self.data[key] = CIPDataStructure(*sub_struct)
                    offset += self.data[key].import_data(bytes, offset).byte_size
        self.byte_size = offset - start_offset
        return self

    def export_data(self):
        data_out = bytearray()
        for key, val in self.structure.items():
            if isinstance(val, str):
                val = CIPDataTypes[val]
            try:
                data_out += self.data[key].export_data()
                continue
            except AttributeError:
                pass
            try:
                data_out += val.export_data(self.data[key])
                continue
            except AttributeError:
                pass
            raise TypeError("No parser for " + key)
        self.byte_size = len(data_out)
        return data_out

    def get_dict(self):
        return self.data

    def pprint(self):
        string_list = []
        for key, val in self.items():
            try:
                tmp = ['\t' + x for x in val.pprint()]
                string_list.append("%s:-" % key)
                string_list += tmp
            except AttributeError:
                string_list.append("%s: %s" % (key, val))
        return string_list

    def print(self):
        return '\n'.join(self.pprint())

class SegType():
    type_code = None
    pass

class PortSegment(SegType):
    type_code = SegmentType.PortSegment

    def __init__(self, port=None, link_address=None, bytes_object=None):
        self.port = port
        self.link_address = link_address
        self.link_address_size = 1
        self.extended_port = False
        self.bytes_object = bytes_object

        if port != None and link_address != None:
            self.bytes_object = self.export_data(port, link_address)

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
        self.bytes_object = data_out
        return data_out

    def export_data(self, port=None, link_address=None):
        self.port         =         port if port != None         else self.port
        self.link_address = link_address if link_address != None else self.link_address

        return self.build(self.port, self.link_address)

    def import_data(self, data, offset=0):
        self.bytes_object = data

    def __str__(self):
        if self.port != None and self.link_address != None:
            return "PortSegment: Port %s, Link %s, Extended %s, Address size %s" % (self.port, self.link_address,
                                                                                    self.extended_port, self.link_address_size)
        return "PortSegment NULL"

class LogicalSegment(SegType):
    type_code = SegmentType.LogicalSegment

    def __init__(self, logical_type=None, format=None, value=None, extended=None, bytes_object=None):
        self.logical_type = logical_type
        self.format = format
        self.value = value
        self.extended = extended
        self.bytes_object = bytes_object

        if self.logical_type != None and self.format != None and self.value != None:
            self.bytes_object = self.export_data(self.logical_type, self.format, self.value, extended=self.extended)

    def build(self, logical_type, format, value, extended=None):
        data_out = bytearray()
        temp_byte = 0x07 & SegmentType.LogicalSegment
        temp_byte = temp_byte << 3
        temp_byte |= 0x07 & logical_type
        temp_byte = temp_byte << 2
        temp_byte |= 0x03 & format
        data_out = struct.pack('B', temp_byte)
        if logical_type == LogicalType.Special:
            data_out += struct.pack('B', value.version)
            data_out += value.export_data()
            self.bytes_object = data_out
            return data_out

        if logical_type == LogicalType.ExtendedLogical:
            if extended == None : raise ValueError("No extended value provided")
            data_out.append(extended)
        if format == LogicalFormat.bit_8:
            data_out += struct.pack('B', value)
        elif format == LogicalFormat.bit_16:
            data_out += struct.pack('H', value)
        elif format == LogicalFormat.bit_32:
            if (logical_type in (LogicalType.InstanceID, LogicalType.ConnectionPoint)
            or extended in (1, 3, 5, 6)):
                data_out += struct.pack('I', value)
            else:
                raise ValueError("Invalid logical extended type for 32 bit format")
        else:
            raise ValueError("Invalid format parameter")
        self.bytes_object = data_out
        return data_out

    def export_data(self, logical_type=None, format=None, value=None, extended=None):
        self.logical_type   = not_none(logical_type, self.logical_type)
        self.format         = not_none(format, self.format)
        self.value          = not_none(value, self.value)
        self.extended       = not_none(extended, self.extended)
        return self.build(self.logical_type, self.format, self.value, extended=self.extended)

    def import_data(self, data, offset=0):
        self.bytes_object = data

    def __str__(self):
        if self.logical_type != None and self.format != None and self.value != None:
            return "Logical: Type %s, format %s, value %s" % (str(LogicalType(self.logical_type)).split('.')[1],
                                                              str(LogicalFormat(self.format)).split('.')[1],
                                                              self.value)
        return "LogicalSegment NULL"

class DataSegment(SegType):
    type_code = SegmentType.DataSegment

    def __init__(self, type=None,  value=None, bytes_object=None):
        self.type = type
        self.value = value
        self.bytes_object = bytes_object

        if self.type != None and self.value != None:
            self.bytes_object = self.export_data(self.type, self.value)

    def build(self, type, value):
        data_out = bytearray()
        temp_byte = 0x07 & SegmentType.DataSegment
        temp_byte = temp_byte << 5
        temp_byte |= 0x17 & type
        data_out.append(temp_byte)
        length = len(value)//2
        if length <= 255:
            data_out.append(length)
            data_out += value
        else:
            raise IndexError("data too large")
        self.length = length
        return data_out

    def export_data(self, type=None, value=None):
        self.type   = not_none(type, self.type)
        self.value  = not_none(value, self.value)
        return self.build(self.type, self.value)

    def import_data(self, data, offset=0):
        self.bytes_object = data

    def __str__(self):
        if self.type != None and self.value != None:
            return "Data: Type %s, size %s" % (str(DataSubType(self.ype)).split('.')[1],
                                               self.length)
        return "DataSegment NULL"

class EPATH(list):

    def add(self, *args, **kwargs):
        seg_type, *args = args
        if seg_type == SegmentType.PortSegment:
            item = PortSegment(*args, **kwargs)
        elif seg_type == SegmentType.LogicalSegment:
            item = LogicalSegment(*args, **kwargs)
        else:
            raise TypeError("segment type not supported")
        self.append(item)

    def export_data(self):
        data_out = bytearray()
        for e_item in self:
            data_out += e_item.export_data()
        return data_out

    def import_data(self, data, length, offset=0):
        index = offset
        while index < length + offset:
            seg_type = data[index]
            for sub in SegType.__subclasses__():
                if sub.type_code == seg_type:
                    segment = sub()
                    index += segment.import_data(data,
                                                 )
                    self.append(segment).byte_size
                    break
            else:
                raise ValueError("Value not a acceptable segment: " + str(seg_type))
        return index - offset

def not_none(primary, secondary):
    return primary if primary != None else secondary


class BaseDataParser():
    # @staticmethod
    # def _parse(data, byte_size, signed, offset=0):
    #     section = data[offset: offset + byte_size]
    #     return int.from_bytes(section, 'little', signed=signed )
    #
    # @staticmethod
    # def _build(value, byte_size, signed):
    #     return value.to_bytes(byte_size, 'little', signed=signed)

    def import_data(self, data, offset=0, endian='little'):
        section = data[offset: offset + self.byte_size]
        return int.from_bytes(section, endian, signed=self.signed )

    def export_data(self, value, endian='little'):
        return value.to_bytes(self.byte_size, endian, signed=self.signed)


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

        if(string_size % 2):
            self.byte_size += 1

        if self.char_size == 1:
            return section.decode('iso-8859-1')
        elif self.char_size > 1:
            return bytes.decode('utf-8')
        else:
            return u'Error: Incorrect character size defined'

    def export_data(self, string):
        length = len(string)
        out = struct.pack('H', length)
        if self.char_size == 1:
            out += string.encode('iso-8859-1')
        elif self.char_size > 1:
            out += string.encode('utf-8')
        else:
            return u'Error: Incorrect character size defined'

        if(length % 2):
            out += bytes(1)
        return out

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
        #utf_encoded = string_parsed.encode('utf-8')
        return string_parsed

class MAC_CIP(BaseDataParser):
    byte_size = 6
    def __init__(self):
        self.val = []
        pass

    def import_data(self, data, offset=0):
        for i in range(0,6):
            self.val.append(data[offset + i])
        return self

    def export_data(self, value=None):
        self.val = not_none(value ,self.val)
        out = bytearray()
        for v in self.val:
            out += v.to_bytes(1, 'little', signed=False)
        return out

    def __str__(self):
        if len(self.val) == 6:
            return "%02x:%02x:%02x:%02x:%02x:%02x" % tuple(self.val)
        else:
            return "%02x:%02x:%02x:%02x:%02x:%02x" % (0,0,0,0,0,0)

class IPAddress_CIP(BaseDataParser):

    def __init__(self):
        self.val = None
        self.parser = UDINT_CIP()
        self.byte_size = None

    def export_data(self, value=None, endian='little'):
        self.val = not_none(value, self.val)
        return self.parser.export_data(self.val, endian)

    def import_data(self, data, offset=0, endian='little'):
        self.val = self.parser.import_data(data, offset, endian)
        self.byte_size = self.parser.byte_size
        return self

    def __str__(self):
        if self.val:
            return socket.inet_ntoa(struct.pack("!I", self.val))
        else:
            return 'No IP'

class SocketAddress(CIPDataStructureVirtual):
    global_structure  = [('sin_family', 'INT'), ('sin_port', 'UINT'),
                          ('sin_addr', IPAddress_CIP), ('sin_zero', [8,'USINT'])]

    def __init__(self):
        self.sin_family = None
        self.sin_port = None
        self.sin_addr = None
        self.sin_zero = None
        self.byte_size = 0

    def import_data(self, data, offset=0):
        self.byte_size = offset

        self.sin_family = INT_CIP().import_data(data, offset, 'big')
        offset += INT_CIP.byte_size
        self.sin_port = UINT_CIP().import_data(data, offset, 'big')
        offset += UINT_CIP.byte_size
        self.sin_addr = IPAddress_CIP().import_data(data, offset, 'big')
        offset += self.sin_addr.byte_size
        self.sin_zero = ULINT_CIP().import_data(data, offset, 'big')
        offset += ULINT_CIP.byte_size

        self.byte_size = offset - self.byte_size
        return self

    def export_data(self):
        output  = INT_CIP().export_data(self.sin_family, 'big')
        output += UINT_CIP().export_data(self.sin_port, 'big')
        output += self.sin_addr.export_data(endian='big')
        output += ULINT_CIP().export_data(self.sin_zero, 'big')
        self.byte_size = len(output)
        return output

    def keys(self):
        return ('sin_family', 'sin_port', 'sin_addr', 'sin_zero')

    def get_dict(self):
        return self.__dict__

    def items(self):
        return [(k, self.__dict__[k]) for k in self.keys()]

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


class KeySegment_v4(CIPDataStructure):
    version = 4
    global_structure = OrderedDict((
                                    ('Vendor_ID', 'UINT'),
                                    ('Device_Type', 'UINT'),
                                    ('Product_Code', 'UINT'),
                                    ('Major_Revision', 'BYTE'),
                                    ('Minor_Revision', 'USINT'),

                                    ))


