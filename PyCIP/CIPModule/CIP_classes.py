from CIPModule import CIP
from DataTypesModule import *

class Identity_Object(BaseStructureAutoKeys):

    def __init__(self, transport):
        self._transport = transport

        self.Vendor_ID = UINT()
        self.Device_Type = UINT()
        self.Product_Code = UINT()
        self.Revision = Revision()
        self.Status = WORD()
        self.Serial_Number = UDINT()
        self.Product_Name = SHORTSTRING()

        self.update()

    def update(self):
        rsp = self._transport.get_attr_all(1, 1)
        if rsp.CIP.General_Status == 0:
            self.import_data(rsp.data)
