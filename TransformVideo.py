import os
import sys
import time
from ffmpy import FFmpeg
import argparse
from Common import HoonUtils as utils


def transform_video(file_path, trans_path, logger=None):
    if not trans_path:
        trans_path = file_path + '.enc.mp4'

    start_time = time.time()

    if logger:
        logger.info(' transform_video.start transform {} to mpeg({})'.format(file_path, trans_path))

    # os.remove(trans_path)
    # ff = FFmpeg(inputs={file_path: None}, outputs={trans_path: '-y -loglevel quiet -stats -c:v libx264'})
    ff = FFmpeg(inputs={file_path: None}, outputs={trans_path: '-y -c:v libx264'})
    ff.run()
    if logger:
        logger.info(' transform_video.end transform {}:{:f}mb to {}:{:f}mb'.format(
            file_path, os.path.getsize( file_path ) / (1024 * 1024), trans_path,
            os.path.getsize( trans_path ) / (1024 * 1024)))

    elapsed = time.time() - start_time
    if logger:
        logger.info(' transform_video. total elapse {:.4f}'.format( elapsed ) )

    os.system("rm " + file_path)

def parse_arguments(argv):
    parser = argparse.ArgumentParser()

    parser.add_argument("--source", default=None, help="source video filename")
    parser.add_argument("--target", default=None, help="source video filename")

    args = parser.parse_args(argv)
    args.source = utils.unicode_normalize(args.source)
    args.target = utils.unicode_normalize(args.target)

    return args


if __name__ == '__main__':
    args = parse_arguments( sys.argv[1:] )
    transform_video(args.source, args.target)
