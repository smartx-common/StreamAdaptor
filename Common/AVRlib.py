#! /usr/bin/env python
# -*- coding: utf-8 -*-
import os
import sys
import socket
import psutil
import signal
import platform
import time
import Common.HoonUtils as utils
from Common import Logger
import json
import moviepy.editor as mpy
from enum import Enum
import numpy as np
import more_itertools as itools
import cv2
import functools
import traceback

os_type = platform.system()
if os_type == "Darwin":
    START_PROC_PREFIX = " nohup "
    START_PROC_POSTFIX = " > /dev/null 2>&1 & "
elif os_type == "Linux":
    START_PROC_PREFIX = " nohup "
    START_PROC_POSTFIX = " > /dev/null 2>&1 & "
    # START_PROC_POSTFIX = " & "
elif os_type == "Windows":
    START_PROC_PREFIX = " start /min "
    START_PROC_POSTFIX = " "
else:
    START_PROC_PREFIX = " nohup "
    START_PROC_POSTFIX = " > /dev/null 2>&1 & "

PYTHON_PATH = os.path.dirname(sys.executable)
PATH_SETUP = "export PATH=" + PYTHON_PATH + ":$PATH"
LIB_SETUP = "export LIBRARY_PATH=" + PYTHON_PATH + "/../lib${LIBRARY_PATH:+:${LIBRARY_PATH}}"
LD_LIB_SETUP = "export LD_LIBRARY_PATH=" + PYTHON_PATH + "/../lib${LD_LIBRARY_PATH:+:${LD_LIBRARY_PATH}}"
ENV_SETUP = PATH_SETUP + ';' + LIB_SETUP + ';' + LD_LIB_SETUP + ';'
MOD_SERVER_ARGS = " --op_mode server --logging "

RESULT_FILE_EXT = '.rst'
VIDEO_FILE_EXT = '.mp4'
IMAGE_FILE_EXT = '.jpg'
JSON_FILE_EXT = '.json'
TXT_FILE_EXT = '.txt'
MMAP_FILE_EXT = '.mmap'
AVI_FILE_EXT = '.avi'

CLIENT_EXIT = -1
SERVER_START = 0
SERVER_CHECK = 1
SERVER_RUN = 3
SERVER_STOP = 4

sVIDEO = 'VIDEO'
sIMAGE = 'IMAGE'
sSERVER = 'SERVER'
sBOTH = 'BOTH'

IMG_ORG_SUB_FOLDER = "img_org"
IMG_VEH_SUB_FOLDER = "img_veh"
IMG_PLT_SUB_FOLDER = "img_plt"
IMG_FACE_SUB_FOLDER = "img_face"
JSON_IMG_SUB_FOLDER = "json_img"
JSON_VEH_SUB_FOLDER = "json_veh"
TXT_VEH_SUB_FOLDER = "txt_veh"
JSON_FACE_SUB_FOLDER = "json_face"


class ModuleOpMode(Enum):
    video = 0
    image = 1
    server = 2
    client = 3
    standalone = 4
    test = 5
    make_dataset = 6
    check_plate = 7
    ptc_test = 8
    make_ptc = 9
    hangul_test = 10


class ModuleOutputMode(Enum):
    video = 0
    image = 1

def check_port(ip, port):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        # noinspection PyBroadException
        try:
            s.bind((ip, port))
            return False
        except Exception as e:
            print(e)
            return True

def kill_process(port, name="", logger=None):
    for proc in psutil.process_iter():
        try:
            for conns in proc.connections(kind='inet'):
                if conns.laddr.port == port:
                    # noinspection PyBroadException
                    try:
                        proc.send_signal(signal.SIGTERM)
                        proc.send_signal(signal.SIGKILL)
                    except Exception as e:
                        print(e)
                    if logger:
                        logger.info(" > Killed the process {} using {:d} port\n".format(name, port))
                    time.sleep(1)
        except psutil.AccessDenied as ad:
            print(ad)
        except psutil.ZombieProcess as zp:
            print(zp)
        except Exception as e:
            print(e)


def create_video_from_images(img_arr, vid_fname, duration=2, fps=30):
    clips = [mpy.ImageClip(m).set_duration(duration) for m in img_arr]
    concat_clip = mpy.concatenate_videoclips(clips, method='compose')
    concat_clip.write_videofile(vid_fname, fps=fps)
    return True


def save_video_file_from_images(img_arr, vid_fname,
                                duration=2, fps=30,
                                logger=Logger.get_stdout_logger()):
    clips = [mpy.ImageClip(m).set_duration(duration) for m in img_arr]
    concat_clip = mpy.concatenate_videoclips(clips, method='compose')
    concat_clip.write_videofile(vid_fname, fps=fps)
    logger.info(" # save video file from {:d} images, {}.".format(len(img_arr), vid_fname))
    return True

def get_server_socket(ip, port,
                      logger=Logger.get_stdout_logger(), proc_name='', listen_num=5):
    logger.info(" # Getting server socket...")
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_address = (ip, port)
    # logger.info(server_address)
    # check = check_port(ip, port, logger=logger)
    # logger.info(check)
    # if check:
    if check_port(ip, port):  # , logger=logger):
        logger.info(" # Port, {:d}, was already taken. "
                    "The process using {:d} will be killed first.".format(port, port))
        kill_process(port, name=proc_name)

    logger.info(" # Starting up \"{}\" SERVER on {}:{:d}...".format(proc_name, ip, port))
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind(server_address)
    sock.listen(listen_num)

    return sock


def save_video_from_image_array(img_arr, base_fname, out_path=None,
                                vid_duration=2, logger=Logger.get_stdout_logger()):
    if vid_duration <= 0 or not img_arr:
        return

    out_fname = os.path.join(out_path, base_fname) if out_path else base_fname
    out_fname += VIDEO_FILE_EXT

    logger.info(" # save video from {:d} images, {}.".format(len(img_arr), out_fname))
    create_video_from_images(img_arr, out_fname, duration=vid_duration)


def save_txt_file(contents, fname, out_path=None, desc='', logger=Logger.get_stdout_logger()):
    txt_fname = os.path.join(out_path, fname) if out_path else fname
    logger.info(" # save {} file, {}.".format(desc, txt_fname))
    with open(txt_fname, "w") as f:
        f.write(contents)


def get_images_from_video(vid_fname, out_path, frame_interval, logger=Logger.get_stdout_logger()):
    utils.file_exists(vid_fname, exit_=True)
    utils.folder_exists(out_path, exit_=False, create_=True, print_=True)

    logger.info(" # Extract image from video, {}".format(vid_fname))

    vid = mpy.VideoFileClip(vid_fname)
    base_fname = os.path.splitext(os.path.basename(vid_fname))[0]
    i_digit = int(np.log10(vid.duration / frame_interval)) + 1
    n_digit = int(np.log10(vid.duration)) + 3

    for i, s in enumerate(itools.numeric_range(0, vid.duration, frame_interval)):
        frame = vid.get_frame(s)
        time_info = "__" + \
                    "{:0{width}d}".format(i, width=i_digit) + \
                    "__" + \
                    "{:0{width}.1f}sec".format(s, width=n_digit)
        out_fname = os.path.join(out_path, base_fname + time_info + IMAGE_FILE_EXT)
        utils.imwrite(frame, out_fname)
        logger.info(" # save image, {}".format(out_fname))


def save_dict_to_json_file(dict_dat, json_fname, logger=Logger.get_stdout_logger()):
    with open(json_fname, "w") as f:
        json.dump(dict_dat, f)
    logger.info(" # Save dict to json file, {}".format(json_fname))


def show_message(logger, msg, postfix="\n"):
    logger.info(msg)
    return msg + postfix


def get_roi(img, roi, imshow_sec=-1, clockwise_=True):
    roi = np.array(roi)
    roi = roi * np.array(img.shape[1::-1]) if not sum(sum(roi > 1)) else roi
    if clockwise_:
        roi[[2, 3]] = roi[[3, 2]]

    roi_corners = np.array([[tuple(x) for x in roi]], dtype=np.int32)
    ignore_mask_color = (255,) * img.shape[2]
    mask = cv2.fillPoly(np.zeros(img.shape, dtype=np.uint8), roi_corners, color=ignore_mask_color)
    roi_img = cv2.bitwise_and(img, mask)
    utils.imshow(roi_img, desc="roi image", pause_sec=imshow_sec)

    # gray_img = cv2.cvtColor(roi_img, code=cv2.COLOR_RGB2GRAY)
    offset = [[0, 0], list(img.shape[1::-1])]

    return roi_img, offset


def norm_rect(rect, max_shape):
    return [0 if rect[0] < 0 else rect[0],
            0 if rect[1] < 0 else rect[1],
            max_shape[0] if rect[2] > max_shape[0] else rect[2],
            max_shape[1] if rect[3] > max_shape[1] else rect[3]]


def put_roi_to_db_format(quad, width, height):
    quad_norm = [[int(p[0] / width * 1000) / 1000., int(p[1] / height * 1000) / 1000.] for p in quad]
    return ','.join(map(str, functools.reduce(lambda x, y: x + y, quad_norm)))


def get_roi_from_db_format(roi_str, width, height):
    quad_norm = np.array([float(x) for x in roi_str.split(',')]).reshape((4, 2)).tolist()
    return [[p[0] * width, p[1] * height] for p in quad_norm]
