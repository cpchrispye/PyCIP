from CIPModule import CIP
from DataTypesModule.DataTypes import *
from DataTypesModule.DataParsers import *

class Identity_Object():

    def __init__(self, transport, **kwargs):
        self.transport = transport
        self.struct = CIPDataStructure(
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
        )
        self.update()

    def update(self):
        rsp = self.transport.get_attr_all(1, 1)
        if rsp.CIP.General_Status == 0:
            self.struct.import_data(rsp.data)
            self.__dict__.update(self.struct.get_dict())

    def pprint(self):
        print('\n'.join(self.struct.pprint()))
