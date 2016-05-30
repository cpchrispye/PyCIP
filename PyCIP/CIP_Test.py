import ENIPModule.ENIP
import CIPModule.CIP
from DataTypesModule.DataTypes import *
from DataTypesModule.DataParsers import *
from CIPModule.CIP_classes import Identity_Object
from CIPModule.DLR_class import DLR_Object
from CIPModule.connection_manager_class import ConnectionManager


session = ENIPModule.ENIP.ENIP_Originator('192.168.0.115' )
session.register_session()


CIP_layer = CIPModule.CIP.Basic_CIP(session, connected=False)
s = CIP_layer.get_attr_single(1, 1, 1)
cm = ConnectionManager(CIP_layer)

class_p = EPath_item(SegmentType.LogicalSegment, LogicalType.ClassID, LogicalFormat.bit_8, 2)
insta_p = EPath_item(SegmentType.LogicalSegment, LogicalType.InstanceID, LogicalFormat.bit_8, 1)
forward_open = cm.forward_open(class_p, insta_p)
b = CIP_layer.get_attr_single(1, 1, 1)
b = CIP_layer.set_connection(forward_open.OT_connection_ID, forward_open.TO_connection_ID)
b = CIP_layer.get_attr_single(1, 1, 1)

exit()



DLR = DLR_Object(CIP_layer)
ID = Identity_Object(CIP_layer)


i=1