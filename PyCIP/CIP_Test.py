import ENIPModule.ENIP
import CIPModule.CIP
from DataTypesModule.DataTypes import *
from DataTypesModule.DataParsers import *
from CIPModule.CIP_classes import Identity_Object
from CIPModule.DLR_class import DLR_Object
from CIPModule.connection_manager_class import ConnectionManager
import time

session = ENIPModule.ENIP.ENIP_Originator('192.168.0.115')
registered = session.register_session()
if not registered:
    exit()
con = CIPModule.CIP.CIP_Manager(session)

#con.get_attr_single(1,1,1)
ID1 = Identity_Object(con)
ID1.pprint()
print('\n')
DLR = DLR_Object(con)
DLR.pprint()
epath = EPATH()
epath.append(LogicalSegment(LogicalType.ClassID, LogicalFormat.bit_8, 0x67))
epath.append(LogicalSegment(LogicalType.InstanceID, LogicalFormat.bit_8, 0xA1))
epath.append(LogicalSegment(LogicalType.ConnectionPoint, LogicalFormat.bit_8, 0x68))
epath.append(LogicalSegment(LogicalType.ConnectionPoint, LogicalFormat.bit_8, 0x69))
epath.append(DataSegment(0, bytearray([1,2,3,4,5,6,7,8,9])))


#epath = EPATH()
#
# epath.append(LogicalSegment(LogicalType.Special, LogicalFormat.bit_8, KeySegment_v4(
#                                                                                      Vendor_ID=1,
#                                                                                      Device_Type=12,
#                                                                                      Product_Code=203,
#                                                                                      Major_Revision=(2 | 0x80),
#                                                                                      Minor_Revision=1
#                                                                                  )
#                          )
#           )
#epath.append(LogicalSegment(LogicalType.ClassID, LogicalFormat.bit_8, 1))
#epath.append(LogicalSegment(LogicalType.InstanceID, LogicalFormat.bit_8, 1))
#epath.append(LogicalSegment(LogicalType.AttributeID, LogicalFormat.bit_8, 15))

con.forward_open(epath)

session.unregister_session()

i=1