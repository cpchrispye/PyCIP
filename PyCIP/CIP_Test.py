import ENIPModule.ENIP
import CIPModule.CIP
from DataTypesModule.DataTypes import *
from DataTypesModule.DataParsers import *
from CIPModule.CIP_classes import Identity_Object
from CIPModule.DLR_class import DLR_Object
from CIPModule.connection_manager_class import ConnectionManager


session = ENIPModule.ENIP.ENIP_Originator('192.168.0.115' )
session.register_session()

con = CIPModule.CIP.CIP_Manager(session)
con.get_attr_single(1,1,1)
con.forward_open()
con.get_attr_single(1,1,1)
con.get_attr_single(1,1,1, CIPModule.CIP.RoutingType.ExplicitDirect)

DLR = DLR_Object(con)
ID = Identity_Object(con)


i=1