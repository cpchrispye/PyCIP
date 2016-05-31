import ENIPModule.ENIP
import CIPModule.CIP
from DataTypesModule.DataTypes import *
from DataTypesModule.DataParsers import *
from CIPModule.CIP_classes import Identity_Object
from CIPModule.DLR_class import DLR_Object
from CIPModule.connection_manager_class import ConnectionManager


session = ENIPModule.ENIP.ENIP_Originator('192.168.0.25' )
session.register_session()

con = CIPModule.CIP.CIP_Manager(session)
con.get_attr_single(1,1,1)
ID1 = Identity_Object(con)
path = EPath_item(SegmentType.PortSegment, 1, 0)
ps = PortSegment(1,0)
epath = EPATH()
epath.add(LogicalSegment(LogicalType.ClassID, LogicalFormat.bit_8, 1))
epath.add(LogicalSegment(LogicalType.InstanceID, LogicalFormat.bit_8, 1))
epath.add(LogicalSegment(LogicalType.AttributeID, LogicalFormat.bit_8, 15))
con.forward_open(path)

con.get_attr_single(1,1,1)
con.get_attr_single(1,1,1, CIPModule.CIP.RoutingType.ExplicitDirect)

#DLR = DLR_Object(con)
ID2 = Identity_Object(con)


i=1