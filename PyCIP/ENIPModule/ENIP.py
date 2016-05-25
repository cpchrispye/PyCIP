import threading
import socket
import time
import struct
from DataTypesModule.DataParsers import CIPDataStructure
import queue
from DataTypesModule.CPF import *
from .ENIPDataStructures import *

class ENIP_Originator():

    def __init__(self, target_ip, target_port=44818):

        self.target = target_ip
        self.port   = target_port
        self.session_handle = None

        self.stream_connections = []
        self.data_out_queue = queue.Queue(50)

        self.response_buffer = {}
        self.ignoring_sender_context = 1
        self.internal_sender_context = 0
        self.buffer_size_per_sender_context = 5
        self.sender_context = self.ignoring_sender_context + 1

        self.TCP_rcv_buffer = bytearray()

        self.add_stream_connection(target_port)
        self.manage_connection = True
        self.connection_thread = threading.Thread(target=self._manage_connection)
        self.connection_thread.start()

    def get_next_sender_context(self):
        if self.sender_context >= 10000:
            self.sender_context = self.ignoring_sender_context
        self.sender_context += 1
        return self.sender_context

    def add_stream_connection(self, target_port):
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(3)
        s.connect((self.target, target_port))
        s.setblocking(0)
        self.stream_connections.append(s)

    def receive_encap(self, context, time_out_ms=5000):
        sleep_period = 0.005
        while time_out_ms > 0:
            if context in self.response_buffer and not self.response_buffer[context].empty():
                return self.response_buffer[context].get()
            time.sleep(sleep_period)
            time_out_ms -= sleep_period * 1000
        return None

    def send_encap(self, data, send_id=None, receive_id=None):
        CPF_Array = CPF_Items()

        if receive_id == None:
            receive_id = self.ignoring_sender_context

        if send_id != None:
            cmd_code = ENIPCommandCode.SendUnitData
            command_specific = SendUnitData(Interface_handle=0, Timeout=0)
            CPF_Array.append(CPF_ConnectedAddress(Connection_Identifier=send_id))
            CPF_Array.append(CPF_ConnectedData(Length=len(data)))
            context = receive_id
        else:
            cmd_code = ENIPCommandCode.SendRRData
            command_specific = SendRRData(Interface_handle=0, Timeout=0)
            CPF_Array.append(CPF_NullAddress())
            CPF_Array.append(CPF_UnconnectedData(Length=len(data)))
            context = self.get_next_sender_context()
        command_specific_bytes = command_specific.export_data()
        CPF_bytes = CPF_Array.export_data()


        encap_header = ENIPEncapsulationHeader( cmd_code,
                                                len(command_specific_bytes) + len(CPF_bytes) + len(data),
                                                self.session_handle,
                                                0,
                                                context,
                                                0,
                                                )
        encap_header_bytes = encap_header.export_data()

        self._send_encap(encap_header_bytes + command_specific_bytes + CPF_bytes + data)

        if context == self.ignoring_sender_context:
            return None
        return context

    def _send_encap(self, packet):
        self.data_out_queue.put(packet)

    def register_session(self):
        command_specific = RegisterSession(Protocol_version=1, Options_flags=0)
        command_specific_bytes = command_specific.export_data()
        encap_header = ENIPEncapsulationHeader(ENIPCommandCode.RegisterSession,
                                               len(command_specific_bytes),
                                               0,
                                               0,
                                               self.internal_sender_context,
                                               0,
                                               )
        self._send_encap(encap_header.export_data() + command_specific_bytes)

        time_sleep = 5/1000
        timeout = 5.0
        while self.session_handle == None:
            time.sleep(time_sleep)
            timeout -= time_sleep
            if timeout <= 0:
                for s in self.stream_connections:
                    s.close()
                self.manage_connection = False
                break

    def _manage_connection(self):
        while self.manage_connection:
            # sessions may run over multiply TCP connections
            self._class2_3_send_rcv()
            self._ENIP_context_packet_mgmt()
            time.sleep(0.001)

    def _class2_3_send_rcv(self):

        for s in self.stream_connections:
                # receive
                try:
                    self.TCP_rcv_buffer += s.recv(65535)
                except BlockingIOError:
                    pass

                if len(self.TCP_rcv_buffer):
                    # all data from tcp stream will be encapsulated
                    self._import_encapsulated_rcv(self.TCP_rcv_buffer, s)

                # send
                while not self.data_out_queue.empty():
                    try:
                        packet = self.data_out_queue.get()
                    except:
                        pass
                    else:
                        s.send(packet)

    def _ENIP_context_packet_mgmt(self):

        if self.internal_sender_context in self.response_buffer:
            buffer = self.response_buffer[self.internal_sender_context]
            while not buffer.empty():
                try:
                    packet = buffer.get()
                except:
                    pass
                else:
                    if packet.encapsulation_header.Command == ENIPCommandCode.RegisterSession and self.session_handle == None:
                        self.session_handle = packet.encapsulation_header.Session_Handle

                    if packet.encapsulation_header.Command == ENIPCommandCode.UnRegisterSession:
                        self.session_handle = None
                        for s in self.stream_connections:
                            s.close()
                        self.manage_connection = False

    def _import_encapsulated_rcv(self, packet, socket):
        transport = trans_metadata(socket, 'tcp')

        header    = ENIPEncapsulationHeader()
        offset    = header.import_data(packet)
        packet_length = header.Length + header.header_size
        if offset < 0 or packet_length  > len(packet):
            return -1

        parsed_cmd_spc = None
        CPF_Array = None

        if offset < packet_length:
            parsed_cmd_spc = CommandSpecificParser().import_data(packet, header.Command, response=True, offset=offset)
            offset += parsed_cmd_spc.byte_size
        if offset < packet_length:
            CPF_Array = CPF_Items()
            offset += CPF_Array.import_data(packet, offset)

        parsed_packet = TransportPacket( transport,
                                         header,
                                         parsed_cmd_spc,
                                         CPF_Array,
                                         data=packet[offset:packet_length]
                                        )

        if header.Command == ENIPCommandCode.SendUnitData:
            rsp_identifier = CPF_Array[0].Connection_Identifier
        else:
            rsp_identifier = header.Sender_Context

        if rsp_identifier not in self.response_buffer:
            self.response_buffer[rsp_identifier] = queue.Queue(self.buffer_size_per_sender_context)
        self.response_buffer[rsp_identifier].put(parsed_packet)

        del packet[:header.Length + header.header_size]

class trans_metadata():

    def __init__(self, socket, proto):
        self.host = socket.getsockname()
        self.peer = socket.getpeername()
        self.protocall = proto

        self.recevied_time = time.time()

class ENIPEncapsulationHeader():

    ENIPHeaderStruct = '<HHIIQI'

    def __init__(self, Command=None, Length=None, Session_Handle=None, Status=None, Sender_Context=None, Options=0) :

        self.Command        = Command
        self.Length         = Length
        self.Session_Handle = Session_Handle
        self.Status         = Status
        self.Sender_Context = Sender_Context
        self.Options        = Options

    def import_data(self, data, offset=0):
        self.header_size = struct.calcsize(self.ENIPHeaderStruct)
        if len(data) - offset >= self.header_size:
            ENIP_header = struct.unpack(self.ENIPHeaderStruct, data[offset:self.header_size])
            self.Command        = ENIP_header[0]
            self.Length         = ENIP_header[1]
            self.Session_Handle = ENIP_header[2]
            self.Status         = ENIP_header[3]
            self.Sender_Context = ENIP_header[4]
            self.Options        = ENIP_header[5]
            return self.header_size
        return -1

    def export_data(self):
        return struct.pack(self.ENIPHeaderStruct,   self.Command,
                                                    self.Length,
                                                    self.Session_Handle,
                                                    self.Status,
                                                    self.Sender_Context,
                                                    self.Options
                            )

