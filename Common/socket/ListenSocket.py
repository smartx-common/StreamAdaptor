import socket
import multiprocessing

from Common.socket.Socket import Socket
from Common import Logger


class ListenSocket:
    def __init__(self, ip, port, logger=Logger.get_stdout_logger(), listen_num=5):
        self.logger = logger
        self.ip = ip
        self.port = port
        self.listen_sock = self._get_listen_socket(listen_num)
        self._stop_event = multiprocessing.Event()
        self._lock = multiprocessing.Lock()
        self._cond_lock = multiprocessing.Condition(self._lock)

    def _get_listen_socket(self, listen_num=5):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_address = (self.ip, self.port)

        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        try:
            sock.bind(server_address)
        except Exception as e:
            Logger.write_exception_log(self.logger, e)
            return None

        sock.listen(listen_num)

        self.logger.info("listen : {}, {}".format(self.ip, self.port))
        return sock

    def _create_socket_instance(self, conn):
        return Socket(conn=conn, logger=self.logger)

    def bypass_check_data(self, data):
        return None

    def handle_request(self, func):
        while not self._stop_event or not self._stop_event.is_set():
            if not self.listen_sock:
                self.listen_sock = self._get_listen_socket(listen_num=50)

            if not self.listen_sock:
                self.logger.error("failed to listen {}:{}".format(self.ip, self.port))
                return

            conn, client_address = self.listen_sock.accept()
            self.logger.info(" # Connected with {}".format(client_address))
            try:
                connected_socket = self._create_socket_instance(conn)

                data = connected_socket.recv()
                ret_check_recv = self.bypass_check_data(data)
                if ret_check_recv:
                    connected_socket.send(ret_check_recv)
                else:
                    response = func(data)
                    if response:
                        connected_socket.send(response)

            except Exception as e:
                Logger.write_exception_log(self.logger, e, "# handle_request.exception")
                try:
                    self.listen_sock.close()
                except Exception as c_e:
                    self.logger.error(" # close.exception : {}".format(c_e))
                self.listen_sock = None

            finally:
                conn.close()

    def stop(self):
        with self._cond_lock:
            self._stop_event.clear()


class ListenJsonSocket(ListenSocket):
    def __init__(self, ip, port, logger=Logger.get_stdout_logger(), listen_num=1):
        super().__init__(ip, port, logger, listen_num)

    def _create_socket_instance(self, conn):
        from .JsonSocket import JsonSocket
        return JsonSocket(conn=conn, logger=self.logger)

    def bypass_check_data(self, data):
        if "cmd" not in data:
            return None

        cmd = data["cmd"]
        if cmd == "check":
            return {"state": "healthy"}

        return None
