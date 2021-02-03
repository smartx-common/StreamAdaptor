import psutil
import pynvml
import numpy as np
import time
import threading
import multiprocessing

from Common.Logger import *


def _get_gpu_usage(gpu_id):
    handle = pynvml.nvmlDeviceGetHandleByIndex(gpu_id)

    gpu_usage = pynvml.nvmlDeviceGetUtilizationRates(handle)

    gpu_mem = pynvml.nvmlDeviceGetMemoryInfo(handle)
    gpu_mem_usage = gpu_mem.used / gpu_mem.total if gpu_mem.total else 0
    return gpu_usage.gpu, gpu_mem_usage


def get_dev_usage(logger=get_stdout_logger()):
    # cpu_usage_list = psutil.cpu_percent(interval=1, percpu=True)
    cpu_usage = psutil.cpu_percent()

    cpu_integrated_mem_ = psutil.virtual_memory()
    mem_usage = int(cpu_integrated_mem_.used / (1024 * 1024 * 1024))

    pynvml.nvmlInit()
    gpu_count = pynvml.nvmlDeviceGetCount()
    logger.info("Total GPU count: {}".format(gpu_count))

    gpu_usage_list = []
    gpu_mem_usage_list = []
    for gpu_id in range(gpu_count):
        gpu_usage, gpu_mem_usage = _get_gpu_usage(0)
        gpu_usage_list.append(gpu_usage)
        gpu_mem_usage_list.append(gpu_mem_usage * 100)

    gpu_usage = np.mean(gpu_usage_list)
    gpu_mem_usage = np.mean(gpu_mem_usage_list)

    return cpu_usage, mem_usage, gpu_usage, gpu_mem_usage


class AgxMonitor(threading.Thread):
    def __init__(self, logger=get_stdout_logger()):
        threading.Thread.__init__(self)
        
        self.logger = logger
        self.mem_usage = ""
        self.gpu_usage = ""
        self.cpu_usage = ""
        self.gpu_mem_usage = ""

    def run(self):
        from jtop import jtop
    
        with jtop() as jetson:
            while jetson.ok():
                try:
                    use = jetson.ram.get('use')
                    tot = jetson.ram.get('tot')
                    self.mem_usage = str(round(use / tot * 100, 2))
                    self.gpu_usage = str(jetson.gpu.get('val'))
 
                    cpu_usage = 0
                    active_cpu_len = 0
                    for processor, stat in jetson.cpu.items():
                        # check cpu is activated
                        if bool(stat) is True:
                            cpu_usage += stat.get('val')
                            active_cpu_len += 1
                    self.cpu_usage = round(cpu_usage / active_cpu_len, 2)
    
                except Exception as e:
                    self.logger.error("get_agx_usage. Exception:{}".format(e))
                    self.nullifier()
                    continue
            
                time.sleep(1)
            
        # if get out from while, and descriptor returned
        self.logger.error("get_agx_usage. Exception: status can't be retrieved")
        self.nullifier()

        timer = threading.Timer(1, self.run)
        timer.start()

    def nullifier(self):
        self.cpu_usage = ""
        self.gpu_usage = ""
        self.mem_usage = ""
        self.gpu_mem_usage = ""

    def get_recent_status(self):
        return self.cpu_usage, self.mem_usage, self.gpu_usage, self.gpu_mem_usage

