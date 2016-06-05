#import DataTypesModule
from .DataTypes import *
from .DataParsers import *
from abc import abstractmethod, ABCMeta
from enum import IntEnum

class CPF_Codes(IntEnum):

    NullAddress       = 0x00
    ConnectedAddress  = 0xA1
    ListIdentity      = 0x63
    SequencedAddress  = 0x8002
    UnconnectedData   = 0xB2
    ConnectedData     = 0xB1
    OTSockaddrInfo    = 0x8000
    TOSockaddrInfo    = 0x8001

class CPF_Items(list):

    def __init__(self):
        self.Item_count = 0
        self.size = 0
        self.CPF_dict = { CPF_object.type_id:CPF_object for CPF_object in CPF_Item.__subclasses__() }

    def import_data(self, data, offset=0):
        self.Item_count = UINT_CIP().import_data(data, offset)
        self.size += UINT_CIP().byte_size
        offset    += UINT_CIP().byte_size

        for _ in range(self.Item_count):
            CPF_type = UINT_CIP().import_data(data, offset)
            CPF_Item_obj = self.CPF_dict[CPF_type]()
            CPF_Item_obj.import_data(data, offset)

            self.size += CPF_Item_obj.byte_size
            offset    += CPF_Item_obj.byte_size
            self.append(CPF_Item_obj)

        return self.size

    def export_data(self):
        self.Item_count = len(self)
        bytes_out = bytes()
        bytes_out += UINT_CIP().export_data(self.Item_count)

        for CPF in self:
            bytes_out += CPF.export_data()
        return bytes_out

class CPF_Item(CIPDataStructure):
    type_id = None
    global_structure  = OrderedDict((('Type_ID', 'UINT'), ('Length', 'UINT')))
    def __init__(self, **kwargs):
        super().__init__()
        self.Type_ID = self.type_id
        self.Length  = 0
        for k, v in kwargs.items():
            self.__setattr__(k, v)


class CPF_NullAddress(CPF_Item):
    type_id = CPF_Codes.NullAddress

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

class CPF_ConnectedAddress(CPF_Item):
    type_id = CPF_Codes.ConnectedAddress
    global_structure  = OrderedDict((('Type_ID', 'UINT'), ('Length', 'UINT'), ('Connection_Identifier', 'UDINT')))

    def __init__(self,**kwargs):
        super().__init__(**kwargs)
        self.Length = 4


class CPF_SequencedAddress(CPF_Item):
    type_id = CPF_Codes.SequencedAddress
    struct_definition  = [('Type_ID', 'UINT'), ('Length', 'UINT'),
                          ('Connection_Identifier', 'UDINT'), ('Encapsulation_Sequence_Number', 'UDINT')]

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.Length = 8


class CPF_UnconnectedData(CPF_Item):
    type_id = CPF_Codes.UnconnectedData
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

class CPF_ConnectedData(CPF_Item):
    type_id = CPF_Codes.ConnectedData
    def __init__(self, **kwargs):
        super().__init__(**kwargs)