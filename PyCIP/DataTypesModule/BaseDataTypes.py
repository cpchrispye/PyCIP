from DataTypesModule.BaseDataParsers import base_data, base_structure, virtual_base_structure

class BOOL(base_data):
    _byte_size = 1
    _signed = 0

class SINT(base_data):
    _byte_size = 1
    _signed = 1

class INT(base_data):
    _byte_size = 2
    _signed = 1

class DINT(base_data):
    _byte_size = 4
    _signed = 1

class LINT(base_data):
    _byte_size = 8
    _signed = 1

class USINT(base_data):
    _byte_size = 1
    _signed = 0

class UINT(base_data):
    _byte_size = 2
    _signed = 0

class UDINT(base_data):
    _byte_size = 4
    _signed = 0

class ULINT(base_data):
    _byte_size = 8
    _signed = 0

class BYTE(base_data):
    _byte_size = 1
    _signed = 0

class WORD(base_data):
    _byte_size = 2
    _signed = 0

class DWORD(base_data):
    _byte_size = 4
    _signed = 0

class LWORD(base_data):
    _byte_size = 8
    _signed = 0


class ARRAY(list, base_structure):

    def __init__(self, data_type, size=None):
        self._data_type = data_type
        self._size = size

    def import_data(self, data, offset=0, size=None):
        length = len(data)
        start_offset = offset

        if size is None:
            size = self._size

        while offset <= length:
            parser = self._data_type()
            offset += parser.import_data(data, offset)
            self.append(parser)
            if len(self) >= size:
                break

        return offset - start_offset

    def keys(self):
        return range(0, len(self)-1)


class STRING(base_data):

    def __init__(self, char_size=1):
        self._char_size = char_size
        self._byte_size = 0
        self._value

    def import_data(self, data, offset=0):
        start_offset = offset
        section = data[offset: offset + 2]
        offset += 2
        string_size =  int.from_bytes(section, 'little', signed=0 )
        section = data[offset: offset + (self._char_size * string_size)]

        self._byte_size = offset + (self._char_size * string_size)

        if(string_size % 2):
            self._byte_size += 1

        if self._char_size == 1:
            self._value = section.decode('iso-8859-1')
        elif self._char_size > 1:
            self._value =  bytes.decode('utf-8')
        self._byte_size = offset - start_offset
        return self._byte_size

    def export_data(self, string=None):
        if string is None:
            string = self._value
        length = len(string)
        out = USINT().export_data(length)

        if self._char_size == 1:
            out += string.encode('iso-8859-1')
        elif self._char_size > 1:
            out += string.encode('utf-8')

        if(length % 2):
            out += bytes(1)
        self._byte_size = len(out)
        return out

    def sizeof(self):
        self.export_data()
        return self._byte_size

class SHORTSTRING(base_data):

    def __init__(self):
        self._char_size = 1
        self._byte_size = 0
        self._value = None

    def import_data(self, data, offset=0):
        start_offset = offset
        section = data[offset: offset + 1]
        offset += 1
        string_size =  int.from_bytes(section, 'little', signed=0 )
        section = data[offset: offset + (self._char_size * string_size)]
        self.byte_size = offset + (self._char_size * string_size)

        self._value = section.decode('iso-8859-1')
        self._byte_size =  offset - start_offset
        return self._byte_size

    def export_data(self, string=None):
        if string is None:
            string = self._value
        length = len(string)
        out = USINT().export_data(length)
        out += string.encode('iso-8859-1')
        #if(length % 2):
        #    out += bytes(1)
        self._byte_size = len(out)
        return out

    def sizeof(self):
        self.export_data()
        return self._byte_size


class Revision(base_structure):
    def __init__(self):
        self.Major_Revision = USINT()
        self.Minor_Revision = USINT()

    def keys(self):
        return ('Major_Revision', 'Minor_Revision')

class Identity(base_structure):

    def __init__(self):
        self.Vendor_ID = UINT()
        self.Device_Type = UINT()
        self.Product_Code = UINT()
        self.Revision = Revision()
        self.Status = WORD()
        self.Serial_Number = UDINT()
        self.Product_Name = SHORTSTRING()

    def keys(self):
        return (
                'Vendor_ID',
                'Device_Type',
                'Product_Code',
                'Revision',
                'Status',
                'Serial_Number',
                'Product_Name',
                )
    def __bytes__(self):
        return bytes(self.export_data())
