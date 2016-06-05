import ENIPModule.ENIP
import CIPModule.CIP

from DataTypesModule import LogicalSegment, LogicalType, LogicalFormat, DataSegment, EPATH, DataSubType
from CIPModule.CIP_classes import Identity_Object
from CIPModule.DLR_class import DLR_Object
from CIPModule.connection_manager_class import ConnectionManager
import time

def main():
    session = ENIPModule.ENIP.ENIP_Originator('192.168.0.115')
    registered = session.register_session()
    if not registered:
        return
    con = CIPModule.CIP.CIP_Manager(session)
    session.list_identity()
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
    epath.append(DataSegment(DataSubType.SimpleData, bytearray([1,2,3,4,5,6,7,8,9])))

    con.forward_open(epath)

    session.unregister_session()

    i=1

if __name__ == '__main__':
    main()