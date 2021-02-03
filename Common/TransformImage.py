import Common.HoonUtils as utils
import cv2


def make_window_masked_image(self, img, win_pos, color=utils.BLACK, show_sec=-1):
    img = utils.draw_box_on_img( img, win_pos, color=color, thickness=-1, alpha=0 )
    utils.imshow( img, desc="make window masked image", pause_sec=show_sec )

    return img


def make_face_masked_image(img, face_pos_arr, color=utils.RED, margin=0, show_sec=-1):
    if face_pos_arr is None:
        return img

    for face_pos in face_pos_arr:
        pos = [face_pos[0] - margin, face_pos[1] - margin, face_pos[2] + margin, face_pos[3] + margin]
        pos = utils.check_box_boundary( pos, img.shape[1::-1] )
        img = utils.draw_box_on_img( img, pos, color=color, thickness=-1, alpha=0 )

    utils.imshow( img, desc="make face masked image", pause_sec=show_sec )

    return img


def make_window_boxed_image(img, veh_feats, color=None, show_sec=-1):
    for veh_idx, veh_feat in enumerate(veh_feats):
        if veh_feat.win_conf_arr:
            color = utils.get_color(i=veh_idx, primary_=False) if color is None else color
            for win_idx, win_pos in enumerate( veh_feat.win_pos_arr ):
                img = utils.draw_quadrilateral_on_image(img, win_pos, color=color, thickness=4)
                text = "{}: {:2d}".format( "Window", veh_feat.win_conf_arr[win_idx])
                img = cv2.putText(img, text, (win_pos[0], win_pos[1] - 10),
                                  cv2.FONT_HERSHEY_SIMPLEX, 2, color, 4)

    utils.imshow( img, desc="make window boxed image", pause_sec=show_sec )

    return img


def make_face_boxed_image(img, feat, color=utils.RED, thickness=4, alpha=0.5, show_conf_=True):
    if feat.face_pos_arr is None or feat.face_conf_arr is None:
        return img

    thickness = thickness if show_conf_ else -1
    for pos, conf in zip( feat.face_pos_arr, feat.face_conf_arr ):
        img = utils.draw_box_on_img( img, pos, color=color, thickness=thickness, alpha=alpha )
        if show_conf_:
            img = cv2.putText( img, "{:3d}".format( conf ),
                               (pos[0] + 4, pos[3] - 4), cv2.FONT_HERSHEY_SIMPLEX, 1, utils.WHITE, 5 )
            img = cv2.putText( img, "{:3d}".format( conf ),
                               (pos[0] + 4, pos[3] - 4), cv2.FONT_HERSHEY_SIMPLEX, 1, color, 2 )

    return img


WIN_MASKING_AREA_CANDIDATES = ('FULL', 'RIGHT', 'LEFT')


class TransformImage:
    def __init__(self, ini):
        self.win_masking_color = "BLACK"    # BLACK / WHITE
        self.win_masking_area = "LEFT"      # FULL / RIGHT / LEFT
        self.face_masking_color = "BLACK"   # BLACK / WHITE
        self.face_masking_margin = 32

        if 'win_masking_color' in ini:
            self.win_masking_color = eval('utils.' + ini['win_masking_color'].upper())
        if 'win_masking_area' in ini:
            self.win_masking_area = ini['win_masking_area'].upper()
        if 'face_masking_color' in ini:
            self.face_masking_color = eval('utils.' + ini['face_masking_color'].upper())
        if 'face_masking_margin' in ini:
            self.face_masking_margin = int(ini['face_masking_margin'])

        if self.win_masking_area not in WIN_MASKING_AREA_CANDIDATES:
            self.win_masking_area = 'FULL'

    def window_mask(self, img, win_pos, show_sec=-1):
        if self.win_masking_area == 'LEFT':
            win_pos = win_pos[:2] + [win_pos[0] + ((win_pos[2] - win_pos[0]) >> 1), win_pos[3]]
        elif self.win_masking_area == 'RIGHT':
            win_pos = [win_pos[0] + ((win_pos[2] - win_pos[0]) >> 1), win_pos[1]] + win_pos[2:]

        return make_window_masked_image(img, win_pos, self.win_masking_color, show_sec)

    def face_mask(self, img, face_pos_arr):
        return make_face_masked_image(img, face_pos_arr,
                                      color=self.face_masking_color,
                                      margin=self.face_masking_margin,
                                      show_sec=-1)
