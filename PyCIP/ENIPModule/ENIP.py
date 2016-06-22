#from multiprocessing import Queue
from queue import Queue
import socket
from threading import Thread
#from multiprocessing import Process as Thread
import time
from Tools.signaling import Signaler
from .ENIPDataStructures import *
import Tools.networking

class ENIP_Originator():

    def __init__(self, target_ip=None, target_port=44818):

        self.target = target_ip
        self.port   = target_port
        self.session_handle = None
        self.keep_alive_rate_s = 60

        self.stream_connection = None
        self.datagram_connection = None
        self.class2_3_out_queue = Queue(50)
        self.class0_1_out_queue = Queue(50)

        self.ignoring_sender_context = 1
        self.internal_sender_context = 0
        self.internal_buffer = []
        self.sender_context = self.ignoring_sender_context + 1
        self.messager = Signaler()
        self.connection_thread = None

        #self.TCP_rcv_buffer = bytearray()
        if target_ip != None:
            self.create_class_2_3(target_ip, target_port)
    @property
    def connected(self):
        return self.manage_connection

    def get_next_sender_context(self):
        if self.sender_context >= 10000:
            self.sender_context = self.ignoring_sender_context
        self.sender_context += 1
        return self.sender_context

    def start(self):
        self.manage_connection = True
        if self.connection_thread == None:
            self.connection_thread = Thread(target=self._manage_connection, name="Enip_layer")
        if not self.connection_thread.is_alive():
            self.connection_thread.start()

    def stop(self):
        self.manage_connection = False

    def create_class_2_3(self, target_ip, target_port=44818):
        if self.target != None:
            raise Tools.exceptions.IncorrectState("IP address already set, use another layer object for different targets")
        self.target = target_ip
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(3)
        s.connect((self.target, target_port))
        s.setblocking(0)
        self.stream_connection = s
        self.start()

    def create_class_0_1(self, target_ip, target_port=2222):
        self.target = target_ip
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.settimeout(3)
        s.connect((self.target, target_port))
        s.setblocking(0)
        self.datagram_connection = s
        self.start()

    def send_encap(self, data, send_id=None, receive_id=None):
        encap_packet = EncapsulatedPacket()

        if not isinstance(receive_id, int):
            receive_id = self.ignoring_sender_context

        if send_id is None:
            encap_packet.Encapsulation_header.Command(ENIPCommandCode.SendRRData)
            encap_packet.Command_specific_data = SendRRData(Interface_handle=0, Timeout=0)
            encap_packet.CPF.append(DT.CPF_NullAddress())
            encap_packet.CPF.append(DT.CPF_UnconnectedData(Length=len(data)))
        else:
            encap_packet.Encapsulation_header.Command(ENIPCommandCode.SendUnitData)
            encap_packet.Command_specific_data = SendUnitData(Interface_handle=0, Timeout=0)
            encap_packet.CPF.append(DT.CPF_ConnectedAddress(Connection_Identifier=send_id))
            encap_packet.CPF.append(DT.CPF_ConnectedData(Length=len(data)))
        encap_packet.CPF[1].data(data)

        encap_packet.Encapsulation_header.Length(encap_packet.Command_specific_data.sizeof() + encap_packet.CPF.sizeof())
        encap_packet.Encapsulation_header.Session_Handle(self.session_handle)
        encap_packet.Encapsulation_header.Status(0)
        encap_packet.Encapsulation_header.Sender_Context(receive_id)
        encap_packet.Encapsulation_header.Options(0)

        self._send_encap(encap_packet)

        if receive_id == self.ignoring_sender_context:
            return None
        return receive_id

    def _send_encap(self, packet):
        if hasattr(packet, 'export_data'):
            packet = packet.export_data()
        self.class2_3_out_queue.put(packet)

    def register_session(self, target_ip=None):
        if target_ip != None:
            self.create_class_2_3(target_ip)

        cmd_sp = RegisterSession(Protocol_version=1, Options_flags=0)
        encap_packet = EncapsulatedPacket(Command=ENIPCommandCode.RegisterSession,
                                          Length=cmd_sp.sizeof(),
                                          Session_Handle=0,
                                          Status=0,
                                          Sender_Context=self.internal_sender_context,
                                          Options=0)
        encap_packet.Command_specific_data = cmd_sp

        self._send_encap(encap_packet)

        time_sleep = 5/1000
        timeout = 5.0
        while self.session_handle == None:
            time.sleep(time_sleep)
            timeout -= time_sleep
            if timeout <= 0:
                self.stream_connection.close()
                self.manage_connection = False
                return False
        return True

    def unregister_session(self):
        encap_packet = EncapsulatedPacket(Command=ENIPCommandCode.UnRegisterSession,
                                          Length=0,
                                          Session_Handle=0,
                                          Status=0,
                                          Sender_Context=self.internal_sender_context,
                                          Options=0)
        self._send_encap(encap_packet)
        time.sleep(0.2)
        self.stop()

    def NOP(self):
        encap_packet = EncapsulatedPacket(Command=ENIPCommandCode.NOP,
                                  Length=0,
                                  Session_Handle=self.session_handle,
                                  Status=0,
                                  Sender_Context=self.internal_sender_context,
                                  Options=0)
        self._send_encap(encap_packet)

    @staticmethod
    def list_identity(target_ip='255.255.255.255', target_port=44818, udp=True):
        sockets = []
        responses = []
        delay = 1000
        header = ENIPEncapsulationHeader(ENIPCommandCode.ListIdentity, 0, 0, 0, delay, 0)
        data = header.export_data()
        networks = Tools.networking.list_networks()

        for ifc in networks:
            if udp:
                s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                s.bind((ifc, 0))
                s.setblocking(0)
                s.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            else:
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.sendto(data, (target_ip, target_port))
            sockets.append(s)
        time.sleep(1.1*delay/1000)
        packets = []
        for s in sockets:
            try:
                while True:
                    packets.append(s.recv(65535))
            except BlockingIOError:
                pass

        for packet in packets:
            if len(packet) < 42:
                continue
            rsp_header = ENIPEncapsulationHeader()
            offset = rsp_header.import_data(packet)
            li = ListIdentityRsp()
            offset += li.import_data(packet, offset)
            responses.append(li)
        return responses

    # this ideally will use asyncio to manage connections
    def _manage_connection(self):
        self.TCP_rcv_buffers = {}
        delay = 0.001
        time_out = time.time() + self.keep_alive_rate_s * 0.5
        while self.manage_connection:
            self._class0_1_send_rcv()
            self._class2_3_send_rcv()
            self._ENIP_context_packet_mgmt()
            # keep alive the connection from timing out
            if time.time() > time_out:
                time_out = time.time() + self.keep_alive_rate_s * 0.9
                self.NOP()
            time.sleep(delay)

        # close all connections if no longer active
        self.session_handle = None
        for s in (self.stream_connection, self.datagram_connection):
            try:
                s.close()
            except:
                pass
        return None

    def _class2_3_send_rcv(self):
        s = self.stream_connection
        if s != None:
            buffer = self.TCP_rcv_buffers.get(s, bytearray())
            # receive
            try:
                buffer += s.recv(65535)
            except BlockingIOError:
                pass

            if len(buffer):
                # all data from tcp stream will be encapsulated
                self._import_encapsulated_rcv(buffer, s)

            # send
            while not self.class2_3_out_queue.empty():
                try:
                    packet = self.class2_3_out_queue.get()
                except:
                    pass
                else:
                    s.send(packet)

    def _class0_1_send_rcv(self):

        s = self.datagram_connection
        if s != None:
                # receive
                try:
                    datagram_packet = s.recv(65535)
                except BlockingIOError:
                    pass

                if len(datagram_packet):
                    # all data from tcp stream will be encapsulated
                    self._import_IO_rcv(datagram_packet, s)

                # send
                while not self.class0_1_out_queue.empty():
                    try:
                        packet = self.class0_1_out_queue.get()
                    except:
                        pass
                    else:
                        s.send(packet)

    def _ENIP_context_packet_mgmt(self):
        for packet in  self.internal_buffer:

            if packet.Encapsulation_header.Command == ENIPCommandCode.RegisterSession and self.session_handle == None:
                self.session_handle = int(packet.Encapsulation_header.Session_Handle)

            if packet.Encapsulation_header.Command == ENIPCommandCode.UnRegisterSession:
                self.manage_connection = False

    def _import_encapsulated_rcv(self, packet, socket):
        encap_packet = EncapsulatedPacket()
        offset = encap_packet.import_data(packet)

        if encap_packet.Encapsulation_header.Command == ENIPCommandCode.SendUnitData:
            encap_packet.response_id = encap_packet.CPF[0].Connection_Identifier
        else:
            encap_packet.response_id = encap_packet.Encapsulation_header.Sender_Context

        if encap_packet.Encapsulation_header.Command in (ENIPCommandCode.SendUnitData, ENIPCommandCode.SendRRData):
            self.messager.send_message(encap_packet.response_id, encap_packet)

        elif encap_packet.Encapsulation_header.Command in (ENIPCommandCode.RegisterSession, ENIPCommandCode.UnRegisterSession,
                                ENIPCommandCode.NOP, ENIPCommandCode.ListIdentity, ENIPCommandCode.ListServices):
            self.internal_buffer.append(encap_packet)
        else:
            print('unsupported ENIP command')

        del packet[:offset]
        return

    def _import_IO_rcv(self, packet, socket):
        transport = trans_metadata(socket, 'udp')
        packet_length = len(packet)
        if packet_length <= 6:
            return None

        CPF_Array = DT.CPF_Items()
        offset = CPF_Array.import_data(packet)

        parsed_packet = DT.TransportPacket(  transport,
                                             None,
                                             None,
                                             CPF_Array,
                                             data=packet[offset:packet_length]
                                        )

        if len(CPF_Array) and  CPF_Array[0].Type_ID == CPF_Codes.SequencedAddress:
            rsp_identifier = CPF_Array[0].Connection_Identifier
        else:
            return None

        parsed_packet.response_id = rsp_identifier
        self.messager.send_message(rsp_identifier, parsed_packet)

    def __del__(self):
        self.unregister_session()

class trans_metadata():

    def __init__(self, socket, proto):
        self.host = socket.getsockname()
        self.peer = socket.getpeername()
        self.protocall = proto
        self.recevied_time = time.time()



def parse_list_identity(list_identity):
    names = {}
    for device_packet in list_identity:
        # loop through all cip items
        ips = []
        for ifc in device_packet.Target_Items:
            ips.append(ifc.Socket_Address.sin_addr)
        names[str(ifc.Product_Name)] = ips
    return names
