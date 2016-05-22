from CIPModule import CIP
from DataTypesModule.DataTypes import *
from DataTypesModule.DataParsers import *

class Identity_Object():

    def __init__(self, transport, **kwargs):
        self.struct = [
            ('Vendor_ID', 'UINT'),
            ('Device_Type', 'UINT'),
            ('Product_Code', 'UINT'),
            ('Revision', [
                ('Major_Revision', 'USINT'),
                ('Minor_Revision', 'USINT'),
            ]),
            ('Status', 'WORD'),
            ('Serial_Number', 'UDINT'),
            ('Product Name', 'SHORT_STRING')
        ]
        cip_obj = CIP.Basic_CIP(transport, **kwargs)
        rsp = cip_obj.get_attr_all(1, 1)
        data_parser = CIP.CIP_Data_Builder()
        self.__dict__.update(data_parser.Import(rsp.data, self.struct))

class DLR_Object():

    def __init__(self, transport, **kwargs):
        active_node_struct = [
            ('Device_IP_Address', 'UDINT'),
            ('Device_MAC_Address', [6, 'USINT']),
        ]
        self.struct = [
            ('Network_Topology', 'USINT'),
            ('Device_Type', 'USINT'),
            ('Ring_Supervisor_Status', 'USINT'),
            ('Ring_Supervisor_Config', [
                ('Ring_Supervisor_Enable', 'BOOL'),
                ('Ring_Supervisor_Precedence', 'USINT'),
                ('Beacon_Interval', 'UDINT'),
                ('Beacon_Timeout', 'UDINT'),
                ('DLR_VLAN_ID', 'UINT'),
            ]),
            ('Ring_Faults_Count', 'UINT'),
            ('Last_Active_Node_on_Port_1', active_node_struct),
            ('Last_Active_Node_on_Port_2', active_node_struct),
            ('Ring_Protocol_Participants_Count', 'UINT'),
            ('Ring_Protocol_Participants_List', ['Ring_Protocol_Participants_Count', [
                ('Device_IP_Address', 'UDINT'),
                ('Device_MAC_Address', [6, 'USINT'])
            ]]),
            ('Ring_Faults_Count', 'UINT'),
            ('Active_Supervisor_Address', [
                ('Device_IP_Address', 'UDINT'),
                ('Device_MAC_Address', [6, 'USINT'])
            ]),
            ('Active_Supervisor_Precedence', 'USINT'),
            ('Capability Flags', 'DWORD'),

        ]
        self.transport = transport
        self.update()

    def update(self):
        rsp = self.transport.get_attr_all(71, 1)
        if rsp.CIP.General_Status == 0:
            self_parsed_data = CIP_Data_Import(rsp.data, self.struct).data
            self.__dict__.update(self_parsed_data)

