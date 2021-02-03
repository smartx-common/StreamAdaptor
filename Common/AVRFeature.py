#! /usr/bin/env python
# -*- coding: utf-8 -*-
from enum import Enum
import numpy as np


class SystemInputType(Enum):
    video = '0'
    image = '1'


class BustClassCode(Enum):
    unknown = '00'
    green = '10'
    namsan = '20'
    public = '30'
    jemulpo = '40'


class ObjectType(Enum):
    other = 0
    car = 1
    van = 2
    bus = 3
    truck = 4
    plate = 5
    window = 6


class VehicleSide(Enum):  # 차량의 전면/후면
    unknown = 0
    front = 1
    back = 2


class VehicleDir(Enum):  # 지점을 기준으로 진입/진출
    unknown = 0
    entry = 1
    exit = 2


class VehicleType(Enum):
    unknown = 0
    car = 1
    van = 2
    bus = 3
    truck = 4


class VehicleColor(Enum):
    unknown = 0
    white = 1
    silver = 2
    gray = 3
    black = 4
    red = 5
    darkblue = 6
    blue = 7
    yellow = 8
    green = 9
    brown = 10
    pink = 11
    purple = 12
    darkgray = 13
    cyan = 14


class ManagerCode(Enum):
    unknown = '0'
    green = '1'  # 녹색교통
    crowded = '2'  # 혼잡


class CreatorCode(Enum):
    ai = 'AA'
    anpr = 'AN'
    tunnel1 = 'NO'
    tunnel3 = 'NT'


class BustPurposeCode(Enum):
    green = 'GG'
    toll = 'TT'
    park = 'PP'


class PlateType(Enum):
    unknown         = 0
    normal          = 1
    taxi            = 2
    bus             = 3
    old             = 4
    new             = 5
    construction    = 6
    diplomacy_long  = 7
    diplomacy_shot  = 8
    temp            = 9


class CharType(Enum):
    unknown = 0
    digit = 1
    korean = 2
    pattern = 3


class ImageFeature:
    def __init__(self, dict_dat=None):

        self.camera_id = "123456789"  # 카메라 ID (9 자리)
        self.is_namsan = False

        self.frame_no = None
        self.taken_date = None  # 통과시간, 날짜 (8 자리)
        self.taken_time = None  # 통과시간, 시간 (8 자리)
        self.uri = None  # 전체 이미지 경로
        self.input_type = None  # 입력 종류
        self.bust_class = None  # 단속대상 구분

        self.manager = None  # 관리주체 코드 (1 자리)
        self.creator = "AA"  # 생성기관 코드 (2 자리)
        self.bust_purpose = None  # 단속 목적 (2 자리)
        self.desc = None  # 이미지 설명 (1 자리)
        self.serial_num = None  # 생성 기관이 부여하는 개별 일련번호 (8 자리)

        self.mmap_fname = None
        self.mmap_shape = None
        self.roi = None

        self.name = None
        self.proc_time = None

        self.veh_pos_arr = None
        self.veh_conf_arr = None
        self.win_pos_arr = None
        self.win_conf_arr = None
        self.plt_pos_arr = None
        self.plt_side_arr = None
        self.plt_num_arr = None
        self.plt_conf_arr = None
        self.plt_type_arr = None
        self.face_pos_arr = None
        self.face_conf_arr = None

        self.obj_arr = None

        if dict_dat:
            self.put_dict_dat(dict_dat)

    def put_dict_dat(self, dict_dat):
        for key in dict_dat:
            if hasattr(self, key):
                setattr(self, key, dict_dat[key])

    def get_dict_dat(self):
        return self.__dict__

    def set_datetime(self, dt):
        self.taken_date = dt.strftime("%Y%m%d")[:8]
        self.taken_time = dt.strftime("%H%M%S%f")[:8]

    def get_roi_img(self):
        img = np.memmap(self.mmap_fname, dtype='uint8', mode='r', shape=tuple(self.mmap_shape))
        box = [[min(self.roi[0][0], self.roi[2][0]), min(self.roi[0][1], self.roi[1][1])],
               [max(self.roi[1][0], self.roi[3][0]), max(self.roi[2][1], self.roi[3][1])]]
        return img[box[0][1]:box[1][1], box[0][0]:box[1][0]], box[0]


class VehicleFeature:
    enum_attr_dict = {
        "type": VehicleType,
        "color": VehicleColor,
        "veh_side": VehicleSide,
        "veh_dir": VehicleDir,
        "plt_type": PlateType
    }

    def __init__(self, dict_dat=None):
        self.type = VehicleType.unknown  # 차량종류. ObjectDetect(또는 Vehicle Detect)에서 기입한다.
        self.color = VehicleColor.unknown  # 차량색상. ObjectDetect(또는 Vehicle Detect)에서 기입한다.
        self.veh_uri = None  # 차량 이미지 경로(마스킹 포함). veh_pos를 사용해서 RstStorage에서 기입한다.
        self.veh_side = VehicleSide.unknown  # 차량 전면/후면. ObjectDetect(또는 Vehicle Detect)에서 기입한다.
        self.veh_dir = VehicleDir.unknown  # 지점 기준 진입/진출. veh_side과 DB의 진/출입 정보를 사용하여 ImgAVR 또는 RstStorage에서 결정
        self.lane = 1  # 차선정보
        self.proc_time = None  # 인식소요시간. ImgAVR에서 기입한다.
        self.plt_uri = None  # 번호판 이미지 경로. plt_pos를 사용해서 RstStorage에서 기입한다.

        self.mmap_fname = None
        self.mmap_shape = None
        self.roi = None

        self.veh_pos = None
        self.veh_conf = None
        self.win_pos_arr = None
        self.win_conf_arr = None
        self.plt_pos = None
        self.plt_num = None  # 차량번호
        self.plt_conf = None  # 인식신뢰도
        self.plt_type = PlateType.unknown
        self.face_pos_arr = None
        self.face_conf_arr = None

        if dict_dat:
            self.put_dict_dat(dict_dat)

    def _set_attr_data(self, name, value):
        if not hasattr(self, name):
            return

        if name in VehicleFeature.enum_attr_dict:
            enum_class = VehicleFeature.enum_attr_dict[name]
            value = enum_class[value]

        setattr(self, name, value)

    def _get_attr_data(self, name):
        attr_value = getattr(self, name)
        if name in VehicleFeature.enum_attr_dict:
            return attr_value.name
        else:
            return attr_value

    def put_dict_dat(self, dict_dat):
        for key in dict_dat:
            self._set_attr_data(key, dict_dat[key])

    def get_dict_dat(self):
        ret = dict()
        for key in self.__dict__:
            ret[key] = self._get_attr_data(key)
        return ret

    def get_temp_veh_pos(self, plt_pos, x_ratio=5, y_ratio=20, bottom_space_ratio=2):
        img_h, img_w = self.mmap_shape[:2]
        plate_w = plt_pos[1][0] - plt_pos[0][0]
        vehicle_w = int(plate_w * x_ratio)
        vehicle_x = plt_pos[0][0] - (vehicle_w - plate_w) / 2
        vehicle_x = max(int(vehicle_x), 0)
        vehicle_x_2 = min(vehicle_x + vehicle_w, img_w)

        plate_h = plt_pos[3][1] - plt_pos[0][1]
        vehicle_h = int(plate_h * y_ratio)
        vehicle_y = plt_pos[0][1] - (vehicle_h - plate_h * bottom_space_ratio)
        vehicle_y = max(int(vehicle_y), 0)
        vehicle_y_2 = min(vehicle_y + vehicle_h, img_h)

        return [vehicle_x, vehicle_y, vehicle_x_2, vehicle_y_2]
