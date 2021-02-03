import os
from enum import Enum, auto

from Common.AVRFeature import *


class CameraConnect(Enum):
    usb = 0,
    rtsp = 1,
    video = 2,


class CameraDomain(Enum):
    normal = 0
    domain1 = 1
    domain2 = 2


class CameraDir(Enum):
    entry = 0
    exit = 1
    both = 2


class CameraVehSide(Enum):
    front = 0
    back = 1


def create_info_from_feat_list(camera_id, img_width, img_height, policy_list):
    for camera_policy in policy_list:
        if camera_id is None or camera_policy.camera_id == camera_id:
            return CameraInfo(img_width, img_height, camera_policy)

    return None
