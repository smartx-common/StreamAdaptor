import numpy as np
import shutil
import os
import sys
import argparse
import json
import cv2
import ffmpeg
from PIL import Image, ImageDraw, ImageFont
from Common import HoonUtils as utils


_SIM_PR_PREFIX = "sim_pr_"


class CollectSimulationInfos:
    def __init__(self, camera_info, sim_save_dir, logger):
        self.pd_info_dict = dict()
        self.camera_info = camera_info
        self.sim_save_dir = sim_save_dir

        self.sim_out_dir = self.get_sim_out_dir(edge_uid, sim_save_dir)
        if os.path.isdir(self.sim_out_dir):
            shutil.rmtree(self.sim_out_dir)
        utils.folder_exists(self.sim_out_dir, create_=True)

        self.logger = logger

    @staticmethod
    def get_sim_out_dir(camera_id, sim_save_dir):
        return os.path.join(sim_save_dir, camera_id)

    def get_sim_out_path(self, frame_no):
        return os.path.join(self.sim_out_dir, _SIM_PR_PREFIX + "{}.json".format(frame_no))

    @staticmethod
    def get_sim_pd_infos_path(camera_id, sim_save_dir):
        return os.path.join(sim_save_dir, 'sim_pd_infos_{}.json'.format(camera_id))

    def add_pd_info(self, frame_no, plt_pos_arr):
        if plt_pos_arr:
            self.pd_info_dict[frame_no] = [plt_pos_arr, None]

    def release_pd_infos(self, rtsp_info, img_width, img_height, total_frame):
        self.logger.info('release_pd_infos.start')

        pr_list = self._complete_pd_info_dict()
        # 나중에 다시 영상 만들기 위해 pd 정보를 또하나의 json으로 만들자

        json_dict = {'camera_id': self.camera_info.edge_uid,
                     'roi': self.camera_info.roi,
                     'video_url': self.camera_info.camera_policy.url,
                     'video_width': rtsp_info.width,
                     'video_height': rtsp_info.height,
                     'img_width': img_width,
                     'img_height': img_height,
                     'total_frame': total_frame,
                     'pr_list': pr_list,
                     'pd_info_dict': self.pd_info_dict}

        sim_pd_infos_path = self.get_sim_pd_infos_path(self.camera_info.edge_uid, self.sim_save_dir)
        with open(sim_pd_infos_path, 'w') as fp:
            json.dump(json_dict, fp, indent=4)

        self.logger.info('release_pd_infos.writed pd_info_dict to {}'.format(sim_pd_infos_path))
        return sim_pd_infos_path

    def _complete_pd_info_dict(self):
        pr_list = []
        for fname in os.listdir(self.sim_out_dir):
            name, ext = os.path.splitext(fname)
            if name.startswith(_SIM_PR_PREFIX) and ext == '.json':
                sim_out_path = os.path.join(self.sim_out_dir, fname)
                try:
                    json_dict = json.load(open(sim_out_path, "r"))
                    frame_no = json_dict['frame_no']
                    if frame_no in self.pd_info_dict:
                        plt_list = json_dict['plt_list']
                        self.pd_info_dict[frame_no][1] = plt_list
                    else:
                        plt_list = []
                        self.logger.error("frame {} is not in pd_info_dict".format(frame_no))

                    pr_list.append((frame_no, [plt['plt_num'] for plt in plt_list]))
                except Exception as e:
                    self.logger.error("failed to load {} : {}".format(sim_out_path, e))

        pr_list.sort(key=lambda x: int(x[0]), reverse=True)
        return pr_list


class MakeSimulationVideo:
    def __init__(self, sim_save_dir, logger):
        self.sim_save_dir = sim_save_dir
        self.logger = logger

        self.camera_id = None
        self.camera_roi = None
        self.video_url = None
        self.video_width = None
        self.video_height = None
        self.img_width = None
        self.img_height = None
        self.total_frame = 0

        self.pd_info_dict = None

        self.last_plt_list = None

        self.font_frame_height = 80
        self.font_height = 100
        self.plt_height = self.font_height + 80

        self.frame_no_text_pos = (40, 20)
        self.last_box_tl = (20, self.frame_no_text_pos[1] + self.font_frame_height + 20)
        self.last_text_pos = (self.last_box_tl[0] + 20, self.last_box_tl[1] + 10)
        self.last_plt_pos_y = self.last_text_pos[1] + self.font_height + 40
        self.last_box_br = (self.last_box_tl[0] + 700, self.last_plt_pos_y + self.plt_height)

        self.is_paint_black_box = False

        HANGUL_FONT = "../Common/fonts/SourceHanSerifK-Regular.otf"
        self.font_frame = ImageFont.truetype(HANGUL_FONT, self.font_frame_height)
        self.font = ImageFont.truetype(HANGUL_FONT, self.font_height)

    def load_pd_infos_json(self, sim_pd_infos_path):
        try:
            json_dict = json.load(open(sim_pd_infos_path, "r"))

            self.camera_id = json_dict['camera_id']
            self.camera_roi = json_dict['roi']
            self.video_url = json_dict['video_url']
            self.video_width = json_dict['video_width']
            self.video_height = json_dict['video_height']
            self.img_width = json_dict['img_width']
            self.img_height = json_dict['img_height']
            self.total_frame = json_dict['total_frame']
            pd_info_dict = json_dict['pd_info_dict']

            self.pd_info_dict = dict()
            for key in pd_info_dict:
                pd_info = pd_info_dict[key]
                if pd_info[0]:
                    self.pd_info_dict[int(key)] = pd_info

            return True
        except Exception as e:
            self.logger.error("failed to load {} : {}".format(sim_pd_infos_path, e))
            return False

    # def remake(self):
    #     sim_out_dir = CollectSimulationInfos.get_sim_out_dir(self.camera_id, self.sim_save_dir)
    #     CollectSimulationInfos.complete_pd_info_dict(self.pd_info_dict, sim_out_dir, self.logger)

    def make(self):
        if not self.sim_save_dir:
            return

        video_fname = self.camera_id + '.'
        video_fname += utils.get_datetime().replace(":", "-") + '.mp4'
        video_path = os.path.join(self.sim_save_dir, video_fname)

        if os.path.isfile(video_path):
            shutil.rmtree(video_path)

        self.logger.info("start making video from ImgExtract and ImgAVR. {}".format(video_path))

        if self.total_frame:
            process1 = (
                ffmpeg.input(self.video_url)
                    .output('pipe:',
                            vframes=self.total_frame,
                            format='rawvideo', pix_fmt='rgb24')
                    .run_async(pipe_stdout=True)
            )
        else:
            process1 = (
                ffmpeg.input(self.video_url)
                    .output('pipe:',
                            format='rawvideo', pix_fmt='rgb24')
                    .run_async(pipe_stdout=True)
            )

        process2 = (
            ffmpeg.input('pipe:', format='rawvideo', pix_fmt='rgb24', s='{}x{}'.format(self.video_width,
                                                                                       self.video_height))
                        .output(video_path, pix_fmt='yuv420p')
                        .overwrite_output()
                        .run_async(pipe_stdin=True)
        )

        read_size = self.video_width * self.video_height * 3

        frame_no = 0
        while True:
            in_bytes = process1.stdout.read(read_size)
            if not in_bytes:
                break
            in_frame = (
                np.frombuffer(in_bytes, np.uint8).reshape([self.video_height, self.video_width, 3])
            )

            if self.img_width != self.video_width or self.img_height != self.video_height:
                in_frame = utils.imresize(in_frame, width=self.img_width, height=self.img_height)

            out_frame = self.process_frame(frame_no, in_frame)

            process2.stdin.write(
                out_frame.astype(np.uint8).tobytes()
            )

            if frame_no != 0 and (frame_no % (30 * 60)) == 0:
                self.logger.info("making video. {} th frame writing".format(frame_no))

            frame_no += 1

        process2.stdin.close()
        process1.wait()
        process2.wait()

        self.logger.info("end making video. total:{} frame".format(frame_no))

    def process_frame(self, frame_no, in_frame):
        if frame_no == 1714:
            a = 0

        ret_img = in_frame

        ret_img = self.draw_text(ret_img, self.frame_no_text_pos, "Frame : {}".format(frame_no), font=self.font_frame)

        # 기존 plate 검출을 가지고 있다가 점점 박스 두께를 줄이도록 하며, final 검출 이후엔 없애도록 하자!
        # 그런데, 두개를 동시에 잡았을 땐 어떻게???
        plt_info_list = []
        if frame_no in self.pd_info_dict:
            plt_pos_arr, plt_list = self.pd_info_dict[frame_no]
            for plt_pos in plt_pos_arr:
                plt_pts = utils.transform_quadrilateral_to_rectangle(plt_pos, algo='max', margin=0)
                crop_plt_img = ret_img[plt_pts[0][1]:plt_pts[1][1], plt_pts[0][0]:plt_pts[1][0]]
                plt_info_list.append((plt_pts, crop_plt_img.copy()))

        ret_img = utils.draw_quadrilateral_on_image(ret_img, self.camera_roi, color=utils.GREEN,
                                                    clockwise_=False, thickness=4)

        if len(plt_info_list) > 0:
            # ROI 선들이 번호판위를 지나갈수 있기 때문에 한번더 그려준다.
            for plt_info in plt_info_list:
                pts, crop_plt_img = plt_info
                ret_img[pts[0][1]:pts[1][1], pts[0][0]:pts[1][0]] = crop_plt_img

            # 박스를 그리자!
            ret_img = utils.draw_quadrilateral_on_image(ret_img, plt_pos_arr,
                                                        color=utils.RED,
                                                        clockwise_=True,
                                                        thickness=10)

            if plt_list is not None:
                for idx in range(len(plt_pos_arr)):
                    if idx < len(plt_list):
                        plt_num = plt_list[idx]['plt_num']
                    else:
                        plt_num = "not found"

                    plt_pos = plt_pos_arr[idx]
                    test_box2 = (min(plt_pos[0][0] + 600, ret_img.shape[1]), plt_pos[0][1] - 10)
                    text_box1 = (test_box2[0]-600, plt_pos[0][1] - (self.font_height + 20))
                    ret_img = cv2.rectangle(ret_img, text_box1, test_box2, utils.BLACK, -1)

                    ret_img = self.draw_text(ret_img, (text_box1[0], text_box1[1]), plt_num)

                self.last_plt_list = (plt_info_list, plt_list)

        if self.last_plt_list:
            plt_info_list, plt_list = self.last_plt_list

            box_l = self.last_box_tl[0]
            box_r = self.last_box_br[0]

            text_pos_x = self.last_text_pos[0]
            for idx in range(len(plt_info_list)):
                if idx < len(plt_list):
                    if self.is_paint_black_box:
                        ret_img = cv2.rectangle(ret_img,
                                                (box_l, self.last_box_tl[1]),
                                                (box_r, self.last_box_br[1]),
                                                utils.BLACK, -1)

                    plt_num = plt_list[idx]['plt_num']
                    plt_url = plt_list[idx]['plt_uri']

                    ret_img = self.draw_text(ret_img, (text_pos_x, self.last_text_pos[1]), plt_num)

                    plt_img = utils.imread(plt_url)
                    if plt_img is not None:
                        plt_img = utils.imresize(plt_img, height=self.plt_height)
                        plt_height = plt_img.shape[0]
                        plt_width = plt_img.shape[1]

                        ret_img[self.last_plt_pos_y:self.last_plt_pos_y + plt_height,
                                text_pos_x:text_pos_x + plt_width] = plt_img

                box_l += 700
                box_r += 700
                text_pos_x += 700

        return ret_img

    def draw_text(self, img, pos, text, font=None):
        if not font:
            font = self.font
        pil_img = Image.fromarray(img, 'RGB')
        draw = ImageDraw.Draw(pil_img)
        draw.text(pos, text, font=font, fill=utils.WHITE)
        return np.array(pil_img)


def parse_arguments(argv):
    parser = argparse.ArgumentParser()
    parser.add_argument("--info_path", required=True, help="ini filename")
    parser.add_argument("--save_dir", required=True, help="ini filename")

    args = parser.parse_args(argv)
    args.info_path = utils.unicode_normalize(args.info_path)

    return args


if __name__ == "__main__":
    if len(sys.argv) == 1:
        sys.argv.extend(['--info_path', '/DATA4/AVR/SimAVR/test_10am_32_97/A20210032/sim_pd_infos.json'])
        sys.argv.extend(['--save_dir', '/DATA4/AVR/SimAVR/test_10am_32_97'])

    args = parse_arguments(sys.argv[1:])

    logger = Logger.setup_logger('MakeAVRSimVideo',
                                'MakeAVRSimVideo.')
    inst = MakeSimulationVideo(args.save_dir, logger)

    if inst.load_pd_infos_json(args.info_path):
        inst.make()
    else:
        logger.info( " load_pd_infos_json load" )
