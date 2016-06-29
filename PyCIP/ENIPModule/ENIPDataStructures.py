from DataTypesModule.DataParsers import *
import DataTypesModule as DT
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


class CommandSpecific_Rsp(DT.BaseStructureAutoKeys):
    command = None

class NOP_CS(CommandSpecific_Rsp):
    command = ENIPCommandCode.NOP

class ListIdentity(CommandSpecific_Rsp):
    command = ENIPCommandCode.ListIdentity

class ListInterfaces(CommandSpecific_Rsp):
    command = ENIPCommandCode.ListInterfaces

class RegisterSession(CommandSpecific_Rsp):
    command = ENIPCommandCode.RegisterSession
    def __init__(self, Protocol_version=None, Options_flags=None):
        self.Protocol_version = DT.UINT(Protocol_version)
        self.Options_flags    = DT.UINT(Options_flags)

class UnRegisterSession(CommandSpecific_Rsp):
    command = ENIPCommandCode.UnRegisterSession

class SendRRData(CommandSpecific_Rsp):
    command = ENIPCommandCode.SendRRData
    def __init__(self, Interface_handle=None, Timeout=None):
        self.Interface_handle = DT.UDINT(Interface_handle)
        self.Timeout          = DT.UINT(Timeout)
        self.Encapsulated_packet = DT.CPF_Items()

class SendUnitData(CommandSpecific_Rsp):
    command = ENIPCommandCode.SendUnitData
    def __init__(self, Interface_handle=None, Timeout=None):
        self.Interface_handle = DT.UDINT(Interface_handle)
        self.Timeout          = DT.UINT(Timeout)
        self.Encapsulated_packet = DT.CPF_Items()

class CommandSpecificParser():
    parsers_rsp = {parser.command:parser for parser in CommandSpecific_Rsp.__subclasses__()}

    def __init__(self, command):
        self._command = command

    def get_parser(self):
        return self.parsers_rsp[self._command]


class ENIPEncapsulationHeader(DT.BaseStructureAutoKeys):

    def __init__(self, Command=None, Length=None, Session_Handle=None, Status=None, Sender_Context=None, Options=0) :

        self.Command        = DT.UINT(Command)
        self.Length         = DT.UINT(Length)
        self.Session_Handle = DT.UDINT(Session_Handle)
        self.Status         = DT.UDINT(Status)
        self.Sender_Context = DT.ULINT(Sender_Context)
        self.Options        = DT.UDINT(Options)

class EncapsulatedPacket(DT.BaseStructure):

    def __init__(self, **kwargs) :
        self.Encapsulation_header  = ENIPEncapsulationHeader(**kwargs)
        self.Command_specific_data = CommandSpecificParser(self.Encapsulation_header.Command)

        self.response_id = None

    @property
    def CPF(self):
        try:
            return self.Command_specific_data.Encapsulated_packet
        except AttributeError:
            return None
    @CPF.setter
    def CPF(self, val):
        self.Command_specific_data.Encapsulated_packet = val

    @property
    def CIP(self):
        try:
            return self.Command_specific_data.Encapsulated_packet[1].data
        except AttributeError:
            return None
    @CIP.setter
    def CIP(self, val):
        self.Command_specific_data.Encapsulated_packet[1].data = val

    @property
    def Response_Data(self):
        try:
            return self.Command_specific_data.Encapsulated_packet[1].data.Response_Data
        except AttributeError:
            return None
    @Response_Data.setter
    def Response_Data(self, val):
        self.Command_specific_data.Encapsulated_packet[1].data.Response_Data = val

    def keys(self):
        return ('Encapsulation_header', 'Command_specific_data')

class IOPacket(DT.BaseStructure):
    def __init__(self, data=None):
        self.CPF = DT.CPF_Items()

        self.response_id = None
        if data is not None:
            self.CPF.import_data(data)

    @property
    def CIP(self):
        return self.CPF[1].data

    @CIP.setter
    def CIP(self, val):
        self.CPF[1].data = val

    @property
    def Response_Data(self):
        try:
            return self.CPF[1].data.Response_Data
        except AttributeError:
            return None

    @Response_Data.setter
    def Response_Data(self, val):
        self.CPF[1].data.Response_Data = val

    def keys(self):
        return ('CPF')

class TargetItems(DT.BaseStructureAutoKeys):

    def __init__(self):
        self.Item_ID        = DT.UINT()
        self.Item_Length    = DT.UINT()
        self.Version        = DT.UINT()
        self.Socket_Address = DT.SocketAddress()
        self.Vendor_ID      = DT.UINT()
        self.Device_Type    = DT.UINT()
        self.Product_Code   = DT.UINT()
        self.Revision       = DT.Revision()
        self.Status         = DT.WORD()
        self.Serial_Number  = DT.UDINT()
        self.Product_Name   = DT.SHORTSTRING()
        self.State          = DT.USINT()


class ListIdentityRsp(DT.BaseStructureAutoKeys):

    def __init__(self):
        self.Item_Count = DT.UINT()
        self.Target_Items = DT.ARRAY(TargetItems, self.Item_Count)