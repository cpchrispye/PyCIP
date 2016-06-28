import ENIPModule
import CIPModule
from DataTypesModule import LogicalSegment, LogicalType, LogicalFormat, DataSegment, EPATH, DataSubType, TransportPacket, CIPServiceCode,\
                            ShortStringDataParser, print_structure, MACAddress
import time

def main():
    # Get a EthNetIP Handler un-initialized
    ENIP_Layer = ENIPModule.ENIP_Originator()

    # broadcast a list identity
    rsp = ENIP_Layer.list_identity()
    devices = ENIPModule.parse_list_identity(rsp)
    print("devices found: " + ', '.join(devices.keys()))

    device_ip = devices['1715-AENTR'][0]
    reply = ENIP_Layer.register_session(str(device_ip))
    if not reply:
        return

    # create a CIP handler with a ENIP layer
    con = CIPModule.CIP_Manager(ENIP_Layer)


    # convenience object can use the CIP handler, they have knowledge of the CIP object structure and services
    ID1 = CIPModule.Identity_Object(con)
    print_structure(ID1)
    print()
    print()


    DLR = CIPModule.DLR_Object(con)
    print(DLR)
    print()


    # CIP handler can perform common services such as get attr,
    # raw rsp come in the form of a Encapsulated packet

    # the structure is as follows:
    data = con.get_attr_single(1, 1, 1)
    print_structure(data)


    # a raw encap send can be used instead of the built in methods

    # first building a EPATH object this is a path to the name field in the identity object
    epath = EPATH()
    epath.append(LogicalSegment(LogicalType.ClassID, LogicalFormat.bit_8, 0x04))
    epath.append(LogicalSegment(LogicalType.InstanceID, LogicalFormat.bit_8, 0x67))
    epath.append(LogicalSegment(LogicalType.ConnectionPoint, LogicalFormat.bit_8, 0x68))
    epath.append(LogicalSegment(LogicalType.ConnectionPoint, LogicalFormat.bit_8, 0x6A))
    epath.append(DataSegment(DataSubType.SimpleData, bytearray([0,0,0,0])))

    # raw send is used along with the service code
    try:
        rsp = con.forward_open(epath, OT_connection_params=0x480A, TO_connection_params=0x4838, trigger=0x01)
        time.sleep(60)

    except Exception as e:
        print(e)
        pass
    con.forward_close()
    ENIP_Layer.unregister_session()


if __name__ == '__main__':
    main()