import ENIPModule
import CIPModule
from DataTypesModule import LogicalSegment, LogicalType, LogicalFormat, DataSegment, EPATH, DataSubType, TransportPacket, CIPServiceCode,\
                            ShortStringDataParser
import time

def main():
    # Get a EthNetIP Handler un-initialized
    ENIP_Layer = ENIPModule.ENIP_Originator()

    # broadcast a list identity
    devices = ENIP_Layer.list_identity()

    reply = False
    # loop through all devices response
    for device_packet in devices:
        # loop through all cip items
        for ifc in device_packet.Target_Items:
            # get ip address
            device_ip = ifc.Socket_Address.sin_addr
            print("connecting to device %s" % device_ip)
            # connect to module
            reply = ENIP_Layer.register_session(str(device_ip))
            if reply:
                print("connected")
                break
            print("failed")
        if reply:
            break
    if not reply:
        return

    # create a CIP handler with a ENIP layer
    con = CIPModule.CIP_Manager(ENIP_Layer)

    # convenience object can use the CIP handler, they have knowledge of the CIP object structure and services
    ID1 = CIPModule.Identity_Object(con)
    print(ID1)
    print()

    DLR = CIPModule.DLR_Object(con)
    print(DLR)
    print()

    # CIP handler can perform common services such as get attr,
    # raw rsp come in the form of a transport packet from DataTypes.TransportPacket
    TransportPacket()
    rsp = con.get_attr_single(1 , 1 , 7)
    # the structure is as follows:
    print("transport header:")
    print(rsp.encapsulation_header.print())
    print("command specific:")
    print(rsp.command_specific.print())
    print("common packet format:")
    print(rsp.CPF.print())
    print("CIP format:")
    print(rsp.CIP.print())
    print("raw data in CIP packet:")
    print(rsp.data)


    # a raw encap send can be used instead of the built in methods

    # first building a EPATH object this is a path to the name field in the identity object
    epath = EPATH()
    epath.append(LogicalSegment(LogicalType.ClassID, LogicalFormat.bit_8, 1))
    epath.append(LogicalSegment(LogicalType.InstanceID, LogicalFormat.bit_8, 1))
    epath.append(LogicalSegment(LogicalType.AttributeID, LogicalFormat.bit_8, 7))

    # raw send if used along with the service code
    rsp = con.raw_CIP_send(CIPServiceCode.get_att_single, epath)

    # check to see if successful before parsing
    if rsp.CIP.General_Status == 0:
        parsed_string = ShortStringDataParser().import_data(rsp.data)
        print(parsed_string)

    # close down
    ENIP_Layer.unregister_session()

    return


if __name__ == '__main__':
    main()