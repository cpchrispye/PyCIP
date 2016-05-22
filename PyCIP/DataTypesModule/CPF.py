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
        self.CPF_dict = { CPF_object.Type_ID:CPF_object for CPF_object in CPF_Item.__subclasses__() }

    def parse(self, data, offset=0):
        self.Item_count = UINT_CIP().parse(data, offset)
        self.size += UINT_CIP().byte_size
        offset    += UINT_CIP().byte_size

        for _ in range(self.Item_count):
            CPF_type = UINT_CIP().parse(data, offset)
            CPF_Item_obj = self.CPF_dict[CPF_type]()
            CPF_Item_obj.Import(data, offset)

            self.size += len(CPF_Item_obj)
            offset    += len(CPF_Item_obj)
            self.append(CPF_Item_obj)

        return self.size

    def Export(self):
        self.Item_count = len(self)
        bytes_out = bytes()
        bytes_out += UINT_CIP().build(self.Item_count)

        for CPF in self:
            bytes_out += CPF.Export()
        return bytes_out

class CPF_Item(BaseStructContainer):
    Type_ID = None
    struct_definition  = [('Type_ID', 'UINT'), ('Length', 'UINT')]

class CPF_NullAddress(CPF_Item):
    Type_ID = CPF_Codes.NullAddress

    def __init__(self, **kwargs):
        self.Length = 0
        super().__init__(**kwargs)

class CPF_ConnectedAddress(CPF_Item):
    Type_ID = CPF_Codes.ConnectedAddress
    struct_definition  = [('Type_ID', 'UINT'), ('Length', 'UINT'), ('Connection_Identifier', 'UDINT')]

    def __init__(self,**kwargs):
        self.Connection_Identifier = None
        self.Length = 4
        super().__init__(**kwargs)

class CPF_SequencedAddress(CPF_Item):
    Type_ID = CPF_Codes.SequencedAddress
    struct_definition  = [('Type_ID', 'UINT'), ('Length', 'UINT'),
                          ('Connection_Identifier', 'UDINT'), ('Encapsulation_Sequence_Number', 'UDINT')]

    def __init__(self, **kwargs):
        self.Connection_Identifier = None
        self.Encapsulation_Sequence_Number = None
        self.Length = 8
        super().__init__(**kwargs)

class CPF_UnconnectedData(CPF_Item):
    Type_ID = CPF_Codes.UnconnectedData

    def __init__(self, **kwargs):
        self.Length = None
        super().__init__(**kwargs)

class CPF_ConnectedData(CPF_Item):
    Type_ID = CPF_Codes.ConnectedData

    def __init__(self, **kwargs):
        self.Length = None
        super().__init__(**kwargs)