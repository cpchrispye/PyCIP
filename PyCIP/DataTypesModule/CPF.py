#import DataTypesModule
from .DataTypes import *
from .DataParsers import *
from abc import abstractmethod, ABCMeta
from DataTypesModule.BaseDataParsers import BaseStructureAutoKeys
from DataTypesModule.BaseDataTypes import *
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

# class CPF_Items(list, CIPDataStructureVirtual):
#
#     def __init__(self):
#         self.Item_count = 0
#         self.size = 0
#         self.CPF_dict = { CPF_object.type_id:CPF_object for CPF_object in CPF_Item.__subclasses__() }
#
#     def import_data(self, data, offset=0):
#         self.Item_count = UINT_CIP().import_data(data, offset)
#         self.size += UINT_CIP().byte_size
#         offset    += UINT_CIP().byte_size
#
#         for _ in range(self.Item_count):
#             CPF_type = UINT_CIP().import_data(data, offset)
#             CPF_Item_obj = self.CPF_dict[CPF_type]()
#             CPF_Item_obj.import_data(data, offset)
#
#             self.size += CPF_Item_obj.byte_size
#             offset    += CPF_Item_obj.byte_size
#             self.append(CPF_Item_obj)
#
#         return self.size
#
#     def export_data(self):
#         self.Item_count = len(self)
#         bytes_out = bytes()
#         bytes_out += UINT_CIP().export_data(self.Item_count)
#
#         for CPF in self:
#             bytes_out += CPF.export_data()
#         return bytes_out
#
#     def keys(self):
#         return range(len(self))
#
#     def get_dict(self):
#         return self
#
# class CPF_Item(CIPDataStructure):
#     type_id = None
#     global_structure  = OrderedDict((('Type_ID', 'UINT'), ('Length', 'UINT')))
#     def __init__(self, **kwargs):
#         super().__init__()
#         self.Type_ID = self.type_id
#         self.Length  = 0
#         for k, v in kwargs.items():
#             self.__setattr__(k, v)
#
#
# class CPF_NullAddress(CPF_Item):
#     type_id = CPF_Codes.NullAddress
#
#     def __init__(self, **kwargs):
#         super().__init__(**kwargs)
#
# class CPF_ConnectedAddress(CPF_Item):
#     type_id = CPF_Codes.ConnectedAddress
#     global_structure  = OrderedDict((('Type_ID', 'UINT'), ('Length', 'UINT'), ('Connection_Identifier', 'UDINT')))
#
#     def __init__(self,**kwargs):
#         super().__init__(**kwargs)
#         self.Length = 4
#
#
# class CPF_SequencedAddress(CPF_Item):
#     type_id = CPF_Codes.SequencedAddress
#     struct_definition  = [('Type_ID', 'UINT'), ('Length', 'UINT'),
#                           ('Connection_Identifier', 'UDINT'), ('Encapsulation_Sequence_Number', 'UDINT')]
#
#     def __init__(self, **kwargs):
#         super().__init__(**kwargs)
#         self.Length = 8
#
#
# class CPF_UnconnectedData(CPF_Item):
#     type_id = CPF_Codes.UnconnectedData
#     def __init__(self, **kwargs):
#         super().__init__(**kwargs)
#
# class CPF_ConnectedData(CPF_Item):
#     type_id = CPF_Codes.ConnectedData
#     def __init__(self, **kwargs):
#         super().__init__(**kwargs)



class CPF_Item(BaseStructureAutoKeys):
    type_id = None
    def __init__(self, length=0):
        self.Type_ID = UINT(self.type_id)
        self.Length  = UINT(length)

class CPF_NullAddress(CPF_Item):
    type_id = CPF_Codes.NullAddress

class CPF_ConnectedAddress(CPF_Item):
    type_id = CPF_Codes.ConnectedAddress
    def __init__(self, Length=4, Connection_Identifier=None):
        super().__init__(Length)
        self.Connection_Identifier = UDINT(Connection_Identifier)

class CPF_SequencedAddress(CPF_Item):
    type_id = CPF_Codes.SequencedAddress
    def __init__(self, Length=8, Connection_Identifier=None, Encapsulation_Sequence_Number=None):
        super().__init__(Length)
        self.Connection_Identifier         = UDINT(Connection_Identifier)
        self.Encapsulation_Sequence_Number = UDINT(Encapsulation_Sequence_Number)

class CPF_UnconnectedData(CPF_Item):
    type_id = CPF_Codes.UnconnectedData
    def __init__(self, Length=0):
        super().__init__(Length)

class CPF_ConnectedData(CPF_Item):
    type_id = CPF_Codes.ConnectedData
    def __init__(self, Length=0):
        super().__init__(Length)


class CPF_Items(list, BaseStructure):
    _CPF_dict = { CPF_object.type_id:CPF_object for CPF_object in CPF_Item.__subclasses__() }

    def __init__(self):
        self.Item_count = UINT(0)

    def import_data(self, data, offset=0):
        offset += self.Item_count.import_data(data, offset)
        CPF_type = UINT()

        for _ in range(self.Item_count):
            CPF_type.import_data(data, offset)
            CPF_Item_obj = self._CPF_dict[CPF_type]()
            offset += CPF_Item_obj.import_data(data, offset)
            self.append(CPF_Item_obj)
        return self.sizeof()

    def export_data(self):
        self.Item_count(len(self))
        bytes_out = self.Item_count.export_data()
        for CPF in self:
            bytes_out += CPF.export_data()
        return bytes_out

    def keys(self):
        return ['Item_count'] + list(range(0, len(self)))

    def sizeof(self):
        size = self.Item_count.sizeof()
        for i in self:
            size += i.sizeof()
        return size