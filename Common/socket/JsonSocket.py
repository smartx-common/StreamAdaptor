#! /usr/bin/env python
# -*- coding: utf-8 -*-

import json

from Common.socket.Socket import *


class JsonSocket(Socket):
    def __init__(self, conn=None, desc="", logger=get_stdout_logger()):
        super().__init__(conn, desc, logger)

    def __del__(self):
        super().__del__()

    @staticmethod
    def is_json(data):
        try:
            json.loads(data)
            return True
        except ValueError:
            return False

    def send(self, json_dat):
        try:
            data = json.dumps(json_dat)
        except Exception as e:
            write_exception_log(self.logger, e, msg="send")
            return False

        # 데이터 utf-8 인코딩
        data = data.encode('utf-8')
        return super().send(data)

    def recv(self):
        data = super().recv()
        if data is not None:
            try:
                data = data.decode('utf-8')
                if len(data) == 0:
                    self.logger.error("recv data fail")
                    return None
                return json.loads(data)
            except Exception as e:
                write_exception_log(self.logger, e, msg="recv")
                return None
        return None


def json_send_and_recv(ip, port, request_dict, recv_=True,
                       show_send_recv_dat_=False, desc="", logger=get_stdout_logger()):
    sock = JsonSocket(desc=desc, logger=logger)
    ret = sock.send_and_recv(ip, port, request_dict, recv_, show_send_recv_dat_)
    sock.uninitialize()
    del sock

    return ret
