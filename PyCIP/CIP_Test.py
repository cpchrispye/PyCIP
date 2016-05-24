import ENIPModule.ENIP
import CIPModule.CIP
import CIPModule.CIP_classes
import time
session = ENIPModule.ENIP.ENIP_Originator('192.168.0.115')
session.register_session()

CIP_layer = CIPModule.CIP.Basic_CIP(session)
s = CIP_layer.get_attr_single(1, 1, 1)
a = CIP_layer.get_attr_all(1, 1)

DLR = CIPModule.CIP_classes.DLR_Object(CIP_layer)





i=1