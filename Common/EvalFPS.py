import time
import numpy as np
from Common.Logger import *


class EvalFPS:
    def __init__(self, flag=True, prefix="", skip_count=10, float_format="{:3.1f}"):
        self.flag = flag
        self.prefix = prefix

        self.fps_list = []
        """
        self.skip_count = skip_count

        self.fps_count = 0
        self.avg_fps = 0
        """
        self.float_format = float_format

        self.last_check_time = time.time()
        self.frame_count = 0

    def _add(self, fps):
        """
        # FPS 정밀도를 늘리기 위한 skip_count
        if self.skip_count > 0:
            self.skip_count -= 1
            return

        self.fps_count += 1
        self.avg_fps = (self.avg_fps * (self.fps_count - 1) + fps) / self.fps_count
        """

        self.fps_list.append(fps)

        if len(self.fps_list) > 50:
            self.fps_list.pop(0)

    def _get_avg_fps(self):
        return np.mean(self.fps_list)

    def check_frame_rate(self, logger=get_stdout_logger(), frames=1):
        """
        if self.flag:
            self.frame_count += 1

            cur_time = time.time()
            elapse = cur_time - self.last_check_time
            if elapse >= 1.:
                # FPS 정밀도를 늘리기 위해 실제 elapse 로 나눈다.
                last_fps = self.frame_count / elapse

                self._add(last_fps)
                logger.info("{} Video real FPS: {:3.1f}. fps_avg : {:3.1f}".format(self.prefix, last_fps, self.avg_fps))
                self.frame_count = 0
                self.last_check_time = cur_time
        """
        if self.flag:
            self.frame_count += frames

            cur_time = time.time()
            elapse = cur_time - self.last_check_time
            if elapse >= 1.:
                # FPS 정밀도를 늘리기 위해 실제 elapse 로 나눈다.
                last_fps = self.frame_count / elapse

                self._add(last_fps)
                logger.info("{} Video real FPS: {:3.1f}. fps_avg : {:3.1f}".format(self.prefix, last_fps,
                                                                                   self._get_avg_fps()))
                self.frame_count = 0
                self.last_check_time = cur_time

    def __str__(self):
        return self.float_format.format(np.mean(self.fps_list))
