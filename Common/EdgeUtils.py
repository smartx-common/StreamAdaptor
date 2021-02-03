
import os.path
import socket
import uuid

from enum import Enum


class EdgeDevice(Enum):
    server = 0,
    jetson_agx = 100,
    blaize_pcie = 200,
    blaize_som = 201,
    unknown = -1


def get_device_info():

    device = None
    sn = None
    mac = hex(uuid.getnode())[2:].upper()
    hostname = socket.gethostname()

    # Device check
    if os.path.exists('/usr/bin/nvidia-smi'):
        device = EdgeDevice.server
    elif os.path.exists('/sys/firmware/devicetree/base/serial-number'):
        device = EdgeDevice.jetson_agx
        with open('/sys/firmware/devicetree/base/serial-number') as sn_file:
            sn = sn_file.read()[:-1]
    elif os.path.exists('/dev/dri/card0'):
        device = EdgeDevice.blaize_pcie
    elif os.path.exists('/dev/dri/xxxxx'):
        # TODO : SoM S/N Fix
        device = EdgeDevice.blaize_som
    else:
        device = EdgeDevice.unknown
        sn = 'unknown'

    if sn is None:
        sn = mac

    # To dict
    ret = {'device': device,
           'sn': sn,
           'hostname': hostname}

    return ret


def test():
    ret = get_device_info()
    print(ret)
    if ret['device'] is None:
        print('fail device')
        return
    if ret['sn'] is None:
        print('fail sn')
        return
    if ret['hostname'] is None:
        print('fail hostname')
        return

    print('=====TEST PASS=====')


if __name__ == '__main__':
    test()
