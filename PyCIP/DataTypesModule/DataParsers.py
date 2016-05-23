from .DataTypes import *
from collections import OrderedDict


class BaseStructContainer():
    struct_definition = []

    def __init__(self, **kwargs):
        self._original_dict = OrderedDict()
        self.rebuild()
        self.__byte_length = None
        if kwargs:
            self.update_data(**kwargs)

    def rebuild(self):
        self.update_data(**self._rebuild(self.struct_definition, self))

    def _rebuild(self, struct, old_struct=None):

        tmpdict = {}
        for name, type in struct:
            if isinstance(type, list):
                sub_name, sub_data_type = type
                # check to see if first item of new struct has already been passed to define length of following data
                if sub_name in tmpdict:
                    size = tmpdict[sub_name] if tmpdict[sub_name] != None else 0
                    new_struct = [(n, sub_data_type) for n in range(size)]
                # length of array may be stated
                elif isinstance(sub_name, int):
                    new_struct = [(n, sub_data_type) for n in range(sub_name)]
                # otherwise is just sub structure
                else:
                    new_struct = type

                val = self.__dict__.get(name, CIP_Struct())
                tmp_var = self._rebuild(new_struct, val)
                if len(tmp_var):
                    val.update_data(**tmp_var)
                    tmpdict[name] = val
            else:
                val = old_struct.__dict__.get(name, None)
                tmpdict[name] = val
        return tmpdict

    def get_dict(self):
        return self._original_dict

    def Import(self, data, offset=0):
        parsed = CIP_Data_Import(data, self.struct_definition, offset)
        self.update_data(**parsed.data)
        self.__byte_length = parsed.data_length
        return parsed

    def Export(self, **kwargs):
        if kwargs:
            self.add_data(**kwargs)
        byte_stream = CIP_Data_Export(self, self.struct_definition)
        self.__byte_length = len(byte_stream)
        return byte_stream

    def __len__(self):
        return self.__byte_length

    def update_data(self, **kwargs):
        for key, val in self.struct_definition:
            if key in kwargs:
                self._original_dict[key] = kwargs[key]
                self.__dict__[key] = kwargs[key]

    def add_data(self, **kwargs):
        self._original_dict.update(kwargs)
        self.__dict__.update(kwargs)

class CIP_Struct():
    def __init__(self, attributes={}):
        if len(attributes):
            self._original_dict = attributes
            self.__dict__.update(attributes)

    def add_data(self, **kwargs):
        self._original_dict.update(kwargs)
        self.__dict__.update(kwargs)

    def get_dict(self):
        return self._original_dict

class ParsedStructure():

    def __init__(self, data={}, data_length=0, data_offset=0):
        self.data = OrderedDict(data)
        self.data_length = data_length
        self.data_offset = data_offset


def CIP_Data_Import(data, struct, byte_offset=0):
    parsed_data = ParsedStructure()
    offset = byte_offset
    data_length = 0

    for name, data_type in struct:

        if isinstance(data_type, list):
            if isinstance(data_type[0], (str, int)):
                sub_name, sub_data_type = data_type
                # check to see if first item of new struct has already been passed to define length of following data
                if sub_name in parsed_data.data:
                    new_struct = [(n, data_type[1]) for n in range(parsed_data.data[sub_name])]
                    parsed = CIP_Data_Import(data, new_struct, offset)
                    local_data = parsed.data
                # length of array may be stated
                elif isinstance(data_type[0], int):
                    new_struct = [(n, data_type[1]) for n in range(sub_name)]
                    parsed = CIP_Data_Import(data, new_struct, offset)
                    local_data = parsed.data
            # otherwise is just sub structure
            else:
                parsed = CIP_Data_Import(data, data_type, offset)
                local_data = CIP_Struct(parsed.data)

            data_length += parsed.data_length
            offset += parsed.data_length

        else:
            if isinstance(data_type, str):
                data_parser = CIPDataTypes[data_type]
            elif hasattr(data_type, 'parse'):
                data_parser = data_type
            else:
                raise TypeError("Data structure does not offer parser")

            local_data = data_parser.parse(data, offset)
            data_length += data_parser.byte_size
            offset += data_parser.byte_size

        parsed_data.data[name] = local_data
        parsed_data.data_length = data_length
        parsed_data.offset = offset
    return parsed_data

def CIP_Data_Export(value_dict, struct):
    temp_dict = {}
    local_data = bytes()

    # BaseStructContainer is our special continer for store cip data when this is supplied it is treating as a dict
    if isinstance(value_dict, BaseStructContainer):
        value_dict = {**value_dict.__dict__ , **value_dict.__class__.__dict__,}

    for name, data_type in struct:
        data = value_dict[name]

        if isinstance(data_type, list):
            sub_name, sub_data_type = data_type
            # check to see if first item of new struct has already been passed to define length of following data
            if sub_name in value_dict:
                new_struct = [(n, sub_data_type) for n in range(value_dict[sub_name])]
                local_data += CIP_Data_Export(data, new_struct)
            # length of array may be stated
            elif isinstance(sub_name, int):
                new_struct = [(n, sub_data_type) for n in range(sub_name)]
                local_data += CIP_Data_Export(data, new_struct)
            # otherwise is just sub structure
            else:
                local_data = CIP_Data_Export(data, sub_data_type)

        else:
            if isinstance(data_type, str):
                data_parser = CIPDataTypes[data_type]
            elif hasattr(data_type, 'build'):
                data_parser = data_type
            else:
                raise TypeError("Data structure does not offer parser")

            local_data += data_parser.build(data)

    return local_data

