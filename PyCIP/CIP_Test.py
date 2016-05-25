import ENIPModule.ENIP
import CIPModule.CIP
from CIPModule.CIP_classes import Identity_Object
from CIPModule.DLR_class import DLR_Object

session = ENIPModule.ENIP.ENIP_Originator('192.168.0.55')
session.register_session()

CIP_layer = CIPModule.CIP.Basic_CIP(session)
s = CIP_layer.get_attr_single(1, 1, 1)
a = CIP_layer.get_attr_all(1, 1)

DLR = DLR_Object(CIP_layer)
ID = Identity_Object(CIP_layer)


i=1