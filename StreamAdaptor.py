
import argparse
import multiprocessing
import cv2
import time
import Common.HoonUtils as utils
import pyinotify
import multiprocessing
import sys

from Common.Logger import *
from Common.MMapFileManager import MMapFileManager
from Common.socket.JsonSocket import json_send_and_recv
from Common.VehCameraPolicy import CameraConnect

from TransformVideo import *
from setproctitle import setproctitle


_this_folder_ = os.path.dirname(os.path.abspath(__file__))
_this_basename_ = os.path.splitext(os.path.basename(__file__))[0]
INI_FNAME = os.path.join(_this_folder_, _this_basename_ + '.ini')


class VideoCaptureUpdater(pyinotify.ProcessEvent):
    """
    Update Event Handler
    """
    def __init__(self, s, fps: int = 15, input_video_path: str = None):
        super(VideoCaptureUpdater, self).__init__(s)

        self.fps = fps
        self.input_video_path = input_video_path
        self.url = None
        self.cap = None
        self.connect = None
        self.frame_fps = None
        self.move_frame = None

        # First update
        self.update_cap()

    def get_cap(self):
        return self.cap

    def update_cap(self):
        self.process_default(None)

    def process_default(self, event):
        """
        Update captuer object
        """

        # Update policy
        self.url = self.input_video_path
        self.connect = CameraConnect.rtsp

        # (Re)init cap
        self.cap = cv2.VideoCapture(self.url)

        # Set FPS & frame time
        self.frame_fps = float(self.cap.get(5))
        self.move_frame = int(self.frame_fps / self.fps)

        print('Update url :', self.url)
        print('GLOBAL_CAP :', self.cap)
        print('cap FPS :', self.frame_fps)


class StreamAdaptor(multiprocessing.Process):

    def __init__(self, write_video :str = None, limit_time :int = None, input_video_path :str = None):

        # Init ini
        self.ini = utils.get_ini_parameters(INI_FNAME)

        # Init logger
        self.logger = setup_logger_with_ini(self.ini['LOGGER'],
                                            logging_=True,
                                            console_=True)

        # Image size
        self.img_height = None
        self.img_width = None
        self.img_height = int(self.ini['OUT_VIDEO']['height'])
        self.img_width = int(self.ini['OUT_VIDEO']['width'])

        # Init video captuer updater
        status = pyinotify.Stats()
        self.video_capture_updater = VideoCaptureUpdater(status, input_video_path=input_video_path)

        # change process name
        setproctitle("python StreamAdaptor.py in StreamAdaptor")

        # last send socket time
        self.last_send_socket_time = time.time()

        # Write Video
        self.write_video = write_video
        self.video_writer = None
        self.limit_time = limit_time
        self.start_time = time.time()
        if self.write_video is not None:
            self.logger.info('WRITE VIDEO MODE : ON')
            CODEC = cv2.VideoWriter_fourcc(*'XVID')
            self.video_writer = cv2.VideoWriter(self.write_video,
                                                fourcc=CODEC,
                                                fps=float(self.video_capture_updater.frame_fps),
                                                frameSize=(self.img_width, self.img_height))


    def callback_inotify(self):
        print('call!')

    def init_inotify(self, paths: str):
        wm = pyinotify.WatchManager()
        self.notifier = pyinotify.ThreadedNotifier(wm,
                                                   default_proc_fun=self.video_capture_updater)
        self.notifier.start()

    def run(self):

        self.logger.info("Start SA")

        frame_no = 0
        while True:

            # Read frame
            cap = self.video_capture_updater.get_cap()
            if self.video_capture_updater.connect is CameraConnect.video:
                cap.set(cv2.CAP_PROP_POS_FRAMES, frame_no)
            print('cap read start')
            ret, frame = cap.read()
            print('cap read done..')

            # Excpetion
            if ret is False:
                frame_no = 0
                cap = self.video_capture_updater.update_cap()
                self.logger.info('Update cap')
                continue
            if frame is None:
                self.logger.info('frame is None')
                continue

            # Delay
            spf = float(1/self.video_capture_updater.frame_fps)
            delta_t = time.time() - self.last_send_socket_time
            delay = max(spf - delta_t, 0.001)
            if __debug__:
                print('spf : {}'.format(spf))
                print('dt  : {}'.format(delta_t))
                self.logger.info('Delay : {}'.format(delay))
            time.sleep(delay)

            # Next frame
            if self.video_capture_updater.connect is CameraConnect.video:
                frame_no += self.video_capture_updater.move_frame
            else:
                frame_no += 1
            self.last_send_socket_time = time.time()

            # Wrtie video
            if self.write_video:
                self.save_frame(frame, color_fmt='BGR')

            # Timeout
            if self.limit_time is not None:
                if self.limit_time < int(time.time() - self.start_time):
                    self.video_writer.release()
                    self.logger.info('TimeOut, Exit.')

                    trans_path = self.write_video.rsplit( '.', 1 )[0] + '.mp4'
                    transform_video(self.write_video, trans_path, self.logger)
                    # os.remove(file_path)
                    break


    def save_frame(self, frame, color_fmt="RGB"):

        if self.write_video:
            mod_frame = frame
            if color_fmt == "RGB":
                mod_frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
            self.video_writer.write(mod_frame)


if __name__ == '__main__':
    """
    Run main 
    """

    # Parse args
    parser = argparse.ArgumentParser()
    parser.add_argument("--write_video", required=True, default=None, help="Write video file path")
    parser.add_argument("--limit_time", required=True, default=None, type=int, help="Limit time (sec)")
    parser.add_argument("--input_video_path", required=True, default=None, help="input video path, rtsp://..")
    args = parser.parse_args(sys.argv[1:])

    # Run SA
    stream_adaptor = StreamAdaptor(args.write_video, 
                                   limit_time=args.limit_time,
                                   input_video_path=args.input_video_path)
    stream_adaptor.run()

    print('END.')
    exit(0)

