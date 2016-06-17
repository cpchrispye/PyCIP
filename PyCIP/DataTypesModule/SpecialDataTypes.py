from DataTypesModule.BaseDataTypes import *
from DataTypesModule.BaseDataParsers import *
import socket
import struct

class IPAddress(UDINT):

    def __init__(self, value=None, endian='little'):
        self._value = value
        self._endian = endian

    def __str__(self):
        if self._value:
            return socket.inet_ntoa(struct.pack("!I", self._value))
        else:
            return 'No IP'

class MACAddress(ARRAY):

    def __init__(self):
        super().__init__(USINT, 6)

    def __str__(self):
        try:
            return "%02x:%02x:%02x:%02x:%02x:%02x" % tuple([int(x) for x in self])
        except:
            return "%02x:%02x:%02x:%02x:%02x:%02x" % (0,0,0,0,0,0)
    def __repr__(self):
        return self.__str__()