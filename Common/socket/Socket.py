#! /usr/bin/env python
# -*- coding: utf-8 -*-

import socket
import time
from Common.Logger import *


class Socket:
    def __init__(self, conn=None, desc="", logger=get_stdout_logger()):
        self.conn = conn
        self.desc = desc + ": " if desc else ""
        self.logger = logger

    def __del__(self):
        self.uninitialize()

    def uninitialize(self):
        if self.conn:
            self.conn.close()
            del self.conn
        self.conn = None

    def send_and_recv(self, ip, port, request_dict, recv_=True, show_send_recv_dat_=False):
        stt_time = time.time()
        if not self.connect(ip, port):
            return None, time.time()-stt_time

        if not self.send(request_dict):
            return None, time.time()-stt_time

        if show_send_recv_dat_:
            self._write_log(True, "Sent data: {}".format(request_dict))

        if not recv_:
            return None, time.time()-stt_time

        recv_dat = self.recv()
        if show_send_recv_dat_:
            self._write_log(True, "Received data: {}".format(recv_dat))

        return recv_dat, time.time()-stt_time

    def connect(self, ip, port):
        if self.conn:
            self.conn.close()

        self.conn = None

        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_address = (ip, port)

        if port == 50012:
            a = 0
        try:
            sock.connect(server_address)
        except Exception as e:
            self._write_log(False, "exception while connecting to {}".format(server_address))
            write_exception_log(self.logger, e)
            return False

        self._write_log(True, "connected to {}, {}".format(ip, port))

        self.conn = sock
        return True

    def _write_log(self, is_info, msg):
        log_msg = self.desc + msg
        if is_info:
            self.logger.info(log_msg)
        else:
            self.logger.error(log_msg)

    def send(self, dat):
        if not self.conn:
            self._write_log(False, "not connected")
            return False

        # 길이 정보 4바이트 송신
        length = len(dat)
        ret = self.conn.sendall(length.to_bytes(4, byteorder='little'))
        if ret is not None:
            self._write_log(False, "send length fail")
            return False

        # 페이로드 데이터 송신
        try:
            if self.conn.sendall(dat) is not None:
                self._write_log(False, "send data fail")
                return False
            else:
                self._write_log(True, "send data {} bytes".format(length))
                return True
        except Exception as e:
            self._write_log(False, "exception while sending data")
            write_exception_log(self.logger, e)
            return False

    def recv(self):
        if not self.conn:
            self._write_log(False, "not connected")
            return None

        # 길이 정보 4바이트 수신
        length_bytes = self.conn.recv(4)
        if len(length_bytes) == 0:
            self._write_log(False, "receive length fail")
            return None

        length = int.from_bytes(length_bytes, byteorder='little')

        # 페이로드 데이터 수신
        data = self._recv_all(length)
        if not data:
            self._write_log(False, "receive data fail")
            return None

        self._write_log(True, "receive data {} bytes".format(length))
        return data

    # 길이 만큼 받는 함수
    def _recv_all(self, n):
        # Helper function to recv n bytes or return None if EOF is hit
        dat = bytearray()
        while len(dat) < n:
            packet = self.conn.recv(n - len(dat))
            if not packet:
                return None
            dat.extend(packet)

        return dat


def send_and_recv(ip, port, request_dict, recv_=True,
                  show_send_recv_dat_=False, desc="", logger=get_stdout_logger()):
    sock = Socket(desc=desc, logger=logger)
    ret = sock.send_and_recv(ip, port, request_dict, recv_, show_send_recv_dat_)
    sock.uninitialize()
    del sock

    return ret
