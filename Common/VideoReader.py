import cv2

import Common.HoonUtils as utils
from Common.MMapFileManager import MMapFileManager


class VideoReader:
    def __init__(self, url, mmap_shape=None, fps=15):
        self.url = url

        self.mmap = None
        if mmap_shape is not None:
            self.mmap_fname = 'video_mmap_fname'
            self.mmap = MMapFileManager()
            mmap_ini = dict()
            mmap_ini['mmap_file_dir'] = 'video_reader_mmap'
            mmap_ini['mmap_file_num'] = 1
            mmap_ini['mmap_file_prefix'] = 'video'
            self.mmap.init_mmap_files('./', mmap_ini, mmap_shape=mmap_shape)

        self.total_frame = None

        # url = '/home/lesit/A10100027.avi'
        self.vid_cap = cv2.VideoCapture(url)
        if not self.vid_cap.isOpened():
            print(" @ Error: OpenCV VideoCapture is not opened with {}".format(url))
            del self.vid_cap
            self.vid_cap = None
        else:
            self.frame_shape = (int(self.vid_cap.get(4)), int(self.vid_cap.get(3)), 3)
            self.frame_fps = float(self.vid_cap.get(5))
            self.total_frame = int(self.vid_cap.get(cv2.CAP_PROP_FRAME_COUNT))
            self.move_frame = int(self.frame_fps/fps)

        self.frame_no = 0

    def get_frame_queue(self):
        if not self.vid_cap.isOpened():
            print(" @ Error: OpenCV VideoCapture is not opened with {}.".format(self.url))
            return None
        return self

    def empty(self):
        if self.total_frame is None or self.frame_no >= self.total_frame:
            return True

        return False

    def get(self):
        frame_no = self.frame_no
        self.vid_cap.set(cv2.CAP_PROP_POS_FRAMES, frame_no)

        ret, frame = self.vid_cap.read()
        if ret:
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            if self.mmap is None:
                frame_info = frame
            else:
                if self.mmap.mmap_shape[0] != frame.shape[0] or self.mmap.mmap_shape[1] != frame.shape[1]:
                    frame = utils.imresize(frame, width=self.mmap.mmap_shape[0], height=self.mmap.mmap_shape[1])

                frame_info = self.mmap.write_mmap(frame)

            self.frame_no += self.move_frame
        else:
            frame_info = None

        return frame_no, frame_info

    def get_mmap_shape(self):
        return self.mmap.mmap_shape

    def is_alive(self):
        if self.empty():
            return False

        return True

    def stop_client(self, logger):
        # 맨 앞의 frame 으로 이동
        self.frame_no = 0
