#!/usr/bin/env python
# -*- coding: utf-8 -*-

from enum import Enum
import sys
import socket
import psutil
from Common import Logger
from Common.socket import JsonSocket


class ModuleManagerOpMode(Enum):
    stop = -1
    start = 0
    check = 1
    run = 2


class ServerFeature:
    def __init__(self, name, ip, port, acronym=None):
        self.name = name
        self.ip = ip
        self.port = port
        self.acronym = acronym

        if not self.acronym:
            self.acronym = name


def check_mod_server(ip, port, mod_name="NoName", show_send_recv_dat_=True, logger=Logger.get_stdout_logger()):
    if check_port(ip, port):
        check_rst = False
        try:
            recv = JsonSocket.json_send_and_recv(ip, port, {"cmd": "check"},
                                                 show_send_recv_dat_=show_send_recv_dat_)

            if recv:
                res = recv[0]
                if res is not None and "state" in res and res["state"] == "healthy":
                    check_rst = True
        except Exception as e:
            Logger.write_exception_log(logger, e, "check_mod_server({}, {}, {})".format(ip, port, mod_name))

        if check_rst:
            logger.info(" # {}://{}:{:d} is in healthy state.".format(mod_name, ip, port))
        else:
            logger.info(" # {}://{}:{:d} is NOT in healthy state.".format(mod_name, ip, port))
        return check_rst
    else:
        logger.info(" @ {}://{}:{:d} DOES NOT exist.".format(mod_name, ip, port))
        return False


def check_module_servers(server_features,
                         exit_=False,
                         show_send_recv_dat_=False,
                         logger=Logger.get_stdout_logger()):
    fail_list = []

    for server_feat in server_features:

        if isinstance(server_features, list):
            ip = server_feat.ip
            port = server_feat.port
            # name = server_feat.name
            acronym = server_feat.acronym
        elif isinstance(server_features, dict):
            ip = server_features[server_feat].ip
            port = server_features[server_feat].port
            # name = server_features[server_feat].name
            acronym = server_features[server_feat].acronym
        else:
            ip, port, name, acronym = None, None, None, None

        if not check_mod_server(ip, port, acronym, show_send_recv_dat_=show_send_recv_dat_, logger=logger):
            fail_list.append([ip, port])

    if len(fail_list) > 0:
        if exit_:
            sys.exit(1)

    return len(fail_list) == 0, fail_list


def get_idx_of_server_features_by_module_name(server_features, mod_name):
    return [x.name for x in server_features].index(mod_name)


def check_port(ip, port):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        # noinspection PyBroadException
        try:
            s.bind((ip, port))
            return False
        except Exception as e:
            print('check_port :', e)
            return True


def get_pid_by_port(port):
    for proc in psutil.process_iter():
        try:
            for conns in proc.connections(kind='inet'):
                if conns.laddr.port == port:
                    print("pid of {} is {}".format(port, proc.pid))
                    return proc.pid
        except psutil.AccessDenied as ad:
            print(ad)
        except psutil.ZombieProcess as zp:
            print(zp)
        except Exception as e:
            print(e)

    return None


if __name__ == "__main__":
    print(get_pid_by_port(50011))
