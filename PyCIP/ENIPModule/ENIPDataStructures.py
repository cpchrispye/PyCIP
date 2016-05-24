from DataTypesModule.DataParsers import *
from enum import IntEnum

class MessageType(IntEnum):

    explicitUCMM      = 0x00
    explicitCM        = 0x01
    implicitIO        = 0x02


class ENIPCommandCode(IntEnum):

    NOP               = 0x00
    ListServices      = 0x04
    ListIdentity      = 0x63
    ListInterfaces    = 0x64
    RegisterSession   = 0x65
    UnRegisterSession = 0x66
    SendRRData        = 0x6f
    SendUnitData      = 0x70

class CPF_Codes(IntEnum):

    NullAddress       = 0x00
    ConnectedAddress  = 0xA1
    ListIdentity      = 0x63
    SequencedAddress  = 0x8002
    UnconnectedData   = 0xB2
    ConnectedData     = 0xB1
    OTSockaddrInfo    = 0x8000
    TOSockaddrInfo    = 0x8001

class CommandSpecific_Rsp(CIPDataStructure):
    command = None
    def __init__(self, **kwargs):
        super().__init__()
        for k, v in kwargs.items():
            self.__setattr__(k, v)


class NOP_CS(CommandSpecific_Rsp):
    command = ENIPCommandCode.NOP
    pass

class ListIdentity(CommandSpecific_Rsp):
    command = ENIPCommandCode.ListIdentity
    pass

class ListInterfaces(CommandSpecific_Rsp):
    command = ENIPCommandCode.ListInterfaces
    pass

class RegisterSession(CommandSpecific_Rsp):
    command = ENIPCommandCode.RegisterSession
    global_structure = OrderedDict((
        ('Protocol_version', 'UINT'),
        ('Options_flags', 'UINT'),
    ))

class UnRegisterSession(CommandSpecific_Rsp):
    command = ENIPCommandCode.UnRegisterSession
    pass

class SendRRData(CommandSpecific_Rsp):
    command = ENIPCommandCode.SendRRData
    global_structure = OrderedDict((
        ('Interface_handle', 'UDINT'),
        ('Timeout', 'UINT'),
    ))

class SendUnitData(CommandSpecific_Rsp):
    command = ENIPCommandCode.SendUnitData
    global_structure = OrderedDict((
        ('Interface_handle', 'UDINT'),
        ('Timeout', 'UINT'),
    ))

class CommandSpecificParser():
    parsers_rsp = {parser.command:parser for parser in CommandSpecific_Rsp.__subclasses__()}

    @classmethod
    def import_data(cls, data, command, response=False, offset=0):
        if response:
            data_parser = cls.parsers_rsp[command]()
        else:
            pass
        data_parser.import_data(data, offset)
        return data_parser