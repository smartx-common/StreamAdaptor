#! /usr/bin/env python
import psutil
import sys
import argparse
import signal
from enum import Enum

from Common.Logger import *


def find_name_in_cmd_line(cmd_line, name_list):
    cmd_list = []
    for cmd in cmd_line:
        if cmd and len(cmd) > 0:
            cmd_list.extend(cmd.split(' '))

    if len(cmd_list) == 0:
        return None

    # print('find_name_in_cmd_line:{}'.format(cmd_list))
    name_set = set(name_list)

    for cmd in cmd_list:
        if len(cmd) == 0:
            continue

        if cmd in name_set:
            return cmd
    return None


def kill_process_list(kill_list, logger=get_stdout_logger()):
    print('kill_process_list:{}'.format(kill_list))

    this_pid = os.getpid()

    proc_list = []
    for process in psutil.process_iter():
        if process.pid == this_pid:
            continue

        cmd_line = process.cmdline()
        if find_name_in_cmd_line(cmd_line, kill_list):
            proc_list.append(process)

    for process in proc_list:
        cmd_msg = " > Try kill the process {}".format(process.cmdline())
        try:
            process.send_signal( signal.SIGTERM )
            process.send_signal( signal.SIGKILL )
        except Exception as e:
            cmd_msg += "\n : exception. {}".format(e)

        if logger:
            logger.info(cmd_msg)
        else:
            print(cmd_msg)


def execute_process(sh_fname, base_dir, logger=get_stdout_logger()):
    if base_dir:
        os.chdir(base_dir)

    if sh_fname.startswith('python'):
        live_cmd = sh_fname + ' > /dev/null & '
    else:
        live_cmd = "bash ./" + sh_fname
    logger.info(live_cmd)
    # 실행이 잘 안되는 경우 script에서 '> /dev/null &'를 제외시키고 테스트 해봐야함
    # 대부분 python 에서 import가 안되는 문제였음
    # 특히, 폴더, AVRManager/의 원래 이름은 AVRManager/ 였는데
    # AVRControlServer 에서 AVRServer/run_AVRServer.sh 를 실행시킬때
    # ImgExtract에서 'AVRManager.ModuleLastTimeRecorder import *' 부분이 에러가 생김
    # 아마도 이유는, AVRControlServer 가 AVRManager 폴더 안에서 실행되었는데,
    # 이때 AVRManager.py 가 있기 때문에 이것과 폴더를 헤깔리게 됨으로써 발생한 것 같음
    # 그래서 폴더 AVRManager -> AVRManager 로 변경함
    os.system(live_cmd)


def execute_process_list(alive_list, base_dir, logger=get_stdout_logger()):
    logger.info('execute_process_list.start : {}'.format(alive_list))

    for module in alive_list:
        execute_process(module, base_dir, logger)

    logger.info('execute_module_list.end')


def get_dead_list(check_list):
    check_set = set(check_list)

    for process in psutil.process_iter():
        cmd_line = process.cmdline()
        if len(cmd_line)>0:
            print(cmd_line)
        name = find_name_in_cmd_line(cmd_line, check_set)
        if name:
            check_set.remove(name)
            if len(check_set) == 0:
                break
    return list(check_set)


class OpMode(Enum):
    kill = 0

"""
1. 특정 이름을 가진 프로세스 죽이기
--op_mode kill --fname AVR


"""

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument( "--op_mode", default=OpMode.kill.name, help="operation mode",
                         choices=[x.name for x in OpMode])
    parser.add_argument( "--fname", default=None, help="python filename" )

    args = parser.parse_args(sys.argv[1:])

    if args.op_mode == OpMode.kill.name:
        kill_modules(kill_list=[args.fname])
