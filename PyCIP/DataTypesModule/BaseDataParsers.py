from abc import ABCMeta, abstractmethod

class virtual_base_data():
    __metaclass__ = ABCMeta

    @abstractmethod
    def import_data(self, bytes, offset=0):
        '''
            must convert bytes to internal state, return bytes it used
        '''
        pass
    @abstractmethod
    def export_data(self):
        '''
            must return the internal state in bytes
        '''
        pass
    @abstractmethod
    def sizeof(self):
        '''
            must return size in bytes
        '''
        pass
    @abstractmethod
    def __call__(self, *args, **kwargs):
        '''
            must return internal value if parameters are present it must take them for internal value
        '''
        pass

class virtual_base_structure():
    __metaclass__ = ABCMeta

    @abstractmethod
    def import_data(self, bytes, offset=0):
        '''
            must convert bytes to internal state, return bytes it used
        '''
        pass
    @abstractmethod
    def export_data(self):
        '''
            must return the internal state in bytes
        '''
        pass
    @abstractmethod
    def sizeof(self):
        '''
            must return size in bytes
        '''
        pass
    @abstractmethod
    def keys(self):
        '''
            must return attribute names of the CIP structure in the order of the CIP structure
        '''
        pass
    @abstractmethod
    def items(self):
        '''
            must return tuple of tuple pair attribute, base data type in the order of the CIP structure
        '''
        pass
    @abstractmethod
    def values(self):
        '''
            must return tuple data types in key order
        '''
        pass
    @abstractmethod
    def __getitem__(self, item):
        '''
            must return attributes base data type shall support indexing by number and name
        '''
        pass
    @abstractmethod
    def __setitem__(self, key, value):
        '''
            must set attributes base data type shall support indexing by number and name
        '''
        pass
    @abstractmethod
    def __len__(self):
        '''
            return number of CIP items in structure
        '''
        pass
    @abstractmethod
    def __iter__(self):
        '''
            must iter though all CIP attributes return the base data type in key order
        '''

    @abstractmethod
    def __next__(self):
        return self



class base_data(virtual_base_data):

    _byte_size = 0
    _signed    = None

    def __init__(self, value=None):
        self._value = value

    def import_data(self, data, offset=0, endian='little'):
        section = data[offset: offset + self._byte_size]
        self._value = int.from_bytes(section, endian, signed=self._signed)
        return self._byte_size

    def export_data(self, value=None, endian='little'):
        if value is None:
            value = self._value
        return value.to_bytes(self._byte_size, endian, signed=self._signed)

    def sizeof(self):
        return self._byte_size

    def __call__(self, value):
        self._value = value
        return self._value

    def __str__(self):
        return str(self._value)

    def __bytes__(self):
        return bytes(self.export_data())

class base_structure():

    def import_data(self, bytes, offset=0):
        length = len(bytes)
        start_offset = offset
        for parser in self:
            offset += parser.import_data(bytes, offset)
            if length <= offset:
                break
        return offset - start_offset

    def export_data(self):
        output_stream = bytearray()
        for parser in self:
            output_stream += parser.export_data()
        return output_stream

    def sizeof(self):
        size = 0
        for item in self:
            size += item.sizeof()
        return size

    @abstractmethod
    def keys(self):
        '''
            must return attribute names of the CIP structure in the order of the CIP structure
        '''
        pass

    def items(self):
        try:
            return self._items
        except:
            self._items = tuple([(k, self.__dict__[k]) for k in self.keys()])
        return self._items

    def values(self):
        try:
            return self._values
        except:
            self._values = tuple([self.__dict__[k] for k in self.keys()])
        return self._values

    def dict(self):
        try:
            return self._dict
        except:
            self._dict = {k:self.__dict__[k] for k in self.keys()}
        return self._dict

    def __getitem__(self, item):
        '''
            getitem returns the a base data type not a value
        '''
        if item is str:
            attr = item
        elif item is int:
            attr = self.keys()[item]
        return self.__dict__[attr]

    def __setitem__(self, key, value):
        '''
            setitem sets the a base data type not a value
        '''
        if key is str:
            attr = key
        elif key is int:
            attr = self.keys()[key]
        if not hasattr(value, 'sizeof'):
            raise ValueError("Structure objects must be a data parser")
        self.__dict__[attr] = value

    def __len__(self):
        return len(self.keys())

    def __iter__(self):
        for x in self.values():
            yield x

    def __next__(self):
        return self.values()

    def __bytes__(self):
        return bytes(self.export_data())

    def recalculate(self):
        '''
            for performance items, values are calculated once off the keys.
            if keys are ever modified they must be recalculated
        '''
        del self._items
        del self._values
        del self._dict


class base_structure_auto_keys(base_structure):

    def keys(self):
        try:
            return self._keys
        except:
            self._keys = []
        return self._keys

    def add_key(self, Name):
        try:
            self._keys
        except:
            self._keys = []
        if Name not in self._keys:
            self._keys.append(Name)
            self.recalculate()

    def __setattr__(self, key, value):
        if hasattr(value, 'sizeof'):
            self.add_key(key)
        super().__setattr__(key, value)