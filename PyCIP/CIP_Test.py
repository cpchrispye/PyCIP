import ENIPModule.ENIP
import CIPModule.CIP
from DataTypesModule.DataTypes import *
from DataTypesModule.DataParsers import *
from CIPModule.CIP_classes import Identity_Object
from CIPModule.DLR_class import DLR_Object
from CIPModule.connection_manager_class import ConnectionManager
import time

session = ENIPModule.ENIP.ENIP_Originator('192.168.0.55')
session.register_session()
sp = StringDataParser()
con = CIPModule.CIP.CIP_Manager(session)

message = sp.export_data("blank")
con.set_attr_single(0xf5, 0x01, 0x06, message)
time.sleep(2)
for i in range(1,25):
    for b in range(1, 6):
        time.sleep(0.5)
        start = str(i)
        message = sp.export_data(start)
        con.set_attr_single(0xf5, 0x01, 0x06, message)
        time.sleep(i*0.001)
        for r in range(15):
            end = sp.import_data(con.get_attr_single(0xf5, 0x01, 0x06).data)
            if start == end:
                print("PASSED - tested sleep of %d ms retry %d" % (i, r) )
                break
            else:
                print("FAILED - tested sleep of %d ms retry %d" % (i, r) )
                time.sleep(0.0001)
exit()

#con.get_attr_single(1,1,1)
ID1 = Identity_Object(con)
ID1.pprint()
print('\n')
#DLR = DLR_Object(con)
#DLR.pprint()
epath = EPATH()

epath.append(LogicalSegment(LogicalType.Special, LogicalFormat.bit_8, KeySegment_v4(
                                                                                     Vendor_ID=1,
                                                                                     Device_Type=12,
                                                                                     Product_Code=203,
                                                                                     Major_Revision=(2 | 0x80),
                                                                                     Minor_Revision=1
                                                                                 )
                         )
          )
#epath.append(LogicalSegment(LogicalType.ClassID, LogicalFormat.bit_8, 1))
#epath.append(LogicalSegment(LogicalType.InstanceID, LogicalFormat.bit_8, 1))
#epath.append(LogicalSegment(LogicalType.AttributeID, LogicalFormat.bit_8, 15))
if con.forward_open(epath):
    print("Connection Successful")
else:
    print("Connection Failed")

con.get_attr_single(1,1,1)
con.get_attr_single(1,1,1, CIPModule.CIP.RoutingType.ExplicitDirect)

#DLR = DLR_Object(con)
ID2 = Identity_Object(con)


i=1