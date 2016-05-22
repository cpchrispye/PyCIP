from DataTypesModule.DataParsers import *
from DataTypesModule.DataTypes import *
from enum import IntEnum



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

class CommandSpecific_Rsp(BaseStructContainer):
    command = None
    pass

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
    struct_definition = (
        ('Protocol_version', 'UINT'),
        ('Options_flags', 'UINT'),
    )

class UnRegisterSession(CommandSpecific_Rsp):
    command = ENIPCommandCode.UnRegisterSession
    pass

class SendRRData(CommandSpecific_Rsp):
    command = ENIPCommandCode.SendRRData
    struct_definition = (
        ('Interface_handle', 'UDINT'),
        ('Timeout', 'UINT'),
    )

class SendUnitData(CommandSpecific_Rsp):
    command = ENIPCommandCode.SendUnitData
    struct_definition = (
        ('Interface_handle', 'UDINT'),
        ('Timeout', 'UINT'),
    )

class CommandSpecificParser():
    parsers_rsp = {parser.command:parser for parser in CommandSpecific_Rsp.__subclasses__()}

    @classmethod
    def Import(cls, data, command, response=False, offset=0):
        if response:
            data_parser = cls.parsers_rsp[command]()
        else:
            pass
        data_parser.Import(data, offset)
        return data_parser