import abc

import os
import asyncio
import json

from Common.Logger import *

__author__ = "Kim, Jaewook"
__copyright__ = "Copyright 2019, The AI Vehicle Recognition Project"
__credits__ = ["Kim, Jaewook", "Paek, Hoon"]
__license__ = "GPL"
__version__ = "0.1.0"
__maintainer__ = ["Kim, Jaewook", "Paek, Hoon"]
__email__ = ["jae.kim@mindslab.ai", "hoon.paek@mindslab.ai"]
__status__ = "Development"  # Development / Test / Release.

"""
    1. receive plate recognition informations
    2. receive the policy having camera and edge informations, the update schedule, and etc.
"""

_this_folder_ = os.path.dirname(os.path.abspath(__file__))
_this_basename_ = os.path.splitext(os.path.basename(__file__))[0]


# asyncio socket server/client
class AsyncServerJson(metaclass=abc.ABCMeta):
    def __init__(self, svr_feat, proctitle=None, logger=get_stdout_logger(), debug=False):
        self.logger = logger
        self.debug = debug

        self.svr_feat = svr_feat
        self.proctitle = proctitle

    def run(self):
        if self.proctitle:
            from setproctitle import setproctitle
            setproctitle(self.proctitle)
        asyncio.run(self._run_server(), debug=self.debug)

    async def _run_server(self):
        # 서버를 생성하고 실행
        server = await asyncio.start_server(self._handler, host=self.svr_feat.ip, port=self.svr_feat.port)
        addr = server.sockets[0].getsockname()
        self.logger.info('Serving ON {}'.format(addr))
        async with server:
            # serve_forever()를 호출해야 클라이언트와 연결을 수락
            await server.serve_forever()

    # overriding function
    def bypass_check_data(self, data):  # virtual
        if "cmd" not in data:
            return None

        cmd = data["cmd"]
        if cmd == "check":
            return {"state": "healthy"}

        return None

    @abc.abstractmethod
    def process_request(self, data):     # virtual
        return None

    async def _handler(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
        addr = writer.get_extra_info('peername')
        self.logger.info(f"connected from {addr!r}")

        length_bytes = await reader.read(4)
        if len(length_bytes) == 0:
            self.logger.error("handler. receive length fail")
            writer.close()
            return

        length = int.from_bytes(length_bytes, byteorder='little')

        data = await reader.read(length)
        data = data.decode("utf-8")
        if len(data) == 0:
            self.logger.error("recv data fail")
            writer.close()
            return

        json_data = json.loads(data)

        ret_check_recv = self.bypass_check_data(json_data)
        if ret_check_recv:
            response = ret_check_recv
        else:
            response = self.process_request(json_data)
        if response is not None:
            try:
                data = json.dumps(response)
            except Exception as e:
                Logger.write_exception_log(self.logger, e, msg="failed json dump:{}".format(response))
                writer.close()
                return

            # 데이터 utf-8 인코딩
            data = data.encode('utf-8')

            length = len(data)
            writer.write(length.to_bytes(4, byteorder='little'))
            writer.write(data)
            await writer.drain()
        writer.close()
