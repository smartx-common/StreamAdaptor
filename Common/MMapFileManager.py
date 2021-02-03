#! /usr/bin/env python
# -*- coding: utf-8 -*-

from Common.AVRlib import *
import os
import shutil


class MMapFileManager:
    def __init__(self):
        self.mmap_shape = None
        self.mmap_arr = None
        self.mmap_file_num = None
        self.mmap_idx = None
        self.mmap_filename_list = None
        self.mmap_last_filename = None
        self._mmap_last_frame = None

    def init_mmap_files(self, base_dir, mmap_ini, sub_dir="", mmap_shape=None, logger=Logger.get_stdout_logger()):
        logger.info("init mmap files")

        mmap_file_dir = os.path.join(base_dir, mmap_ini['mmap_file_dir'])
        if sub_dir:
            mmap_file_dir = os.path.join(mmap_file_dir, sub_dir)

        try:
            if utils.folder_exists(mmap_file_dir, exit_=False, create_=False, print_=False):
                shutil.rmtree(mmap_file_dir)
        except Exception as ex:
            logger.error(" @ Error: mmap file dir remove failed[{}] : {}".format(mmap_file_dir, ex))
            sys.exit(1)

        try:
            os.makedirs(mmap_file_dir)
        except Exception as ex:
            logger.error(" @ Error: mmap file dir makedirs failed[{}] : {}".format(mmap_file_dir, ex))
            sys.exit(1)

        self.mmap_idx = 0
        self.mmap_file_num = int(mmap_ini['mmap_file_num'])
        mmap_file_prefix = mmap_ini['mmap_file_prefix']

        if mmap_shape:
            self.mmap_shape = mmap_shape
        else:
            mmap_width = int(mmap_ini['mmap_width'])
            mmap_height = int(mmap_ini['mmap_height'])

            self.mmap_shape = (mmap_height, mmap_width, 3)

        dummy = np.zeros(shape=self.mmap_shape, dtype='uint8')

        self.mmap_filename_list = []
        self.mmap_arr = []
        abs_path = os.path.abspath(mmap_file_dir)
        for i in range(self.mmap_file_num):
            self.mmap_filename_list.append(os.path.join(abs_path, "{}.mmap_{:02d}.mmap".format(mmap_file_prefix, i)))
            mmap = np.memmap(self.mmap_filename_list[i], dtype='uint8', mode='w+', shape=tuple(self.mmap_shape))
            mmap[:] = dummy
            mmap.flush()
            self.mmap_arr.append(mmap)

        logger.info(" # init_mmap_files mmap file dir : {}".format(mmap_file_dir))

    def check_init_mmap(self, base_dir, mmap_ini, prefix, mmap_shape, logger):
        if self.mmap_arr and self.mmap_shape == mmap_shape:
            return

        self.init_mmap_files(base_dir, mmap_ini, prefix, mmap_shape, logger)

    def write_mmap(self, frame):
        self.mmap_arr[self.mmap_idx][:] = frame[:]
        self.mmap_last_filename = self.mmap_filename_list[self.mmap_idx]
        self._mmap_last_frame = self.mmap_arr[self.mmap_idx]
        self.mmap_idx = (self.mmap_idx + 1) % self.mmap_file_num

        return self.mmap_last_filename

    def get_last_frame(self):
        return self._mmap_last_frame

    @staticmethod
    def read_mmap(fname, shape):
        return np.memmap(fname, dtype='uint8', mode='r', shape=tuple(shape))
