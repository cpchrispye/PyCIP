from .DataTypes import *
from collections import OrderedDict

class CIPDataStructure():
    global_structure = OrderedDict()
    def __init__(self, *data_tuple):
        self.structure = OrderedDict(self.global_structure)
        self.structure.update(data_tuple)
        self.keys = self.structure.keys()
        self.byte_size = 0
        self.data = {}

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
            name = self.keys[item]
        return self.data[name]

    def __setitem__(self, key, value):
        name = key
        if isinstance(key, int):
            name = self.keys[key]
        self.data[name] = value

    def __iter__(self):
        for key in self.keys:
            yield self.data[key]

    def items(self):
        return [(key, self.data[key]) for key in self.keys]

    def import_data(self, bytes, offset=0):
        start_offset = offset
        for key, val in self.structure.items():
            try:
                # see if string representation of type is used
                if isinstance(val, str):
                    val = CIPDataTypes[val]
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
                    offset += self.data[key].import_data(bytes, offset)
        self.byte_size = offset - start_offset
        return self.byte_size

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








class CIPDataStructure(object):

    def __init__(self, *struct):
        self.struct = OrderedDict(struct)
        self.data = None
    def __getattr__(self, item):
        if isinstance(item, int):
            return self.data[self.struct[item][0]]
        if item in self.struct:
            return self.data[item]
        return self.__dict__[item]

    def __setattr__(self, key, value):
        if isinstance(key, int):
            self.data[self.struct[key][0]] = value
        else:
            self.data[key] = value

    def import_data(self, data, offset=0):
        for key, val in self.struct.items():
            if hasattr(val, 'parse'):
                # raw data type
                offset += val.byte_size
                self.data[key] = val.parse(data, offset)
            if isinstance(val, (list, tuple)):
                # sub structure fully defined
                if isinstance(val[0], (list, tuple)):
                    sub_struct = self.__class__(*val)
                # defined array
                elif isinstance(val[0], int):
                    sub_struct = self.__class__([(i, val[1])for i in range(val[0])])
                # parameter array
                elif isinstance(val[0], str):
                    size = self.data[val[0]]
                    sub_struct = self.__class__([(i, val[1])for i in range(size)])
                offset += sub_struct.import_data(data, offset)
                self.data[key] = sub_struct


    def export_data(self):
        pass


    pass


