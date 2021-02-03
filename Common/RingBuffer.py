#! /usr/bin/env python
# -*- coding: utf-8 -*-
import threading
import copy


class RingBuffer:
    def __init__(self, size, logger=None, logging_pull_only=True):
        self.size = size
        self.buffer = [None, ] * self.size
        self.write_ptr = 0
        self.read_ptr = 0
        self.logger = logger
        self.logging_pull_only = logging_pull_only

    def debug_log(self, msg):
        if not self.logging_pull_only and self.logger is not None:
            self.logger.info(" RingBuffer.{}. w{:d}, r{:d}".format(msg, self.write_ptr, self.read_ptr))

    def _get_real_index(self, index):
        return index % self.size

    def _move_next(self, index):
        return (index + 1) % self.size

    def write(self, instance):
        # time.sleep(5)  #set writer slower

        self.buffer[self.write_ptr] = instance

        """
        start 변수를 두지 않아도 되지만, 마지막 하나는 사용하지 못한다.
        즉, write가 read보다 빠를 경우 size-1 만큼만 사용하게 됨
        """
        self.write_ptr = self._move_next(self.write_ptr)
        if self.write_ptr == self.read_ptr:
            self.read_ptr = self._move_next(self.read_ptr)

            if self.logger is not None:
                self.logger.info(" RingBuffer.write. No empty buffer. inc r. w{:d}, r{:d}".format(
                    self.write_ptr, self.read_ptr))

    def is_next_full(self):
        return self._move_next(self.write_ptr) == self.read_ptr

    def empty(self):
        return self.read_ptr == self.write_ptr
    
    def read(self):
        # time.sleep(5)  #set reader slower

        # write_ptr 전까지는 read 가능. 즉, write_ptr 이 5이면 4까지는 write 했다는 것임
        if self.empty():
            return None

        assert (self.buffer[self.read_ptr] is not None)
        instance = self.buffer[self.read_ptr]

        self.read_ptr = self._move_next(self.read_ptr)

        return copy.deepcopy(instance)


class ThreadSafeRingBuffer(RingBuffer):
    def __init__(self, size, logger=None, logging_pull_only=True):
        super().__init__(size, logger, logging_pull_only)

        self.lock = threading.Condition()

    def write(self, instance):
        self.debug_log("write:Entering")
        with self.lock:
            self.debug_log("write:Entered")

            super().write(instance)

            # wait 에 들어간 read 함수를 깨운다.
            self.lock.notify()

        self.debug_log("write:Leaved")

    def read(self):
        self.debug_log("read:Entering")

        with self.lock:
            self.debug_log("read:Entered")

            ret = super().read()

            if ret is None:
                self.debug_log("read:Wait")

                self.lock.wait(1)

                self.debug_log("read:Waked")
                # wait이 끝나면, 다시 read 가 호출되어 처리하도록 한다.

            else:
                self.debug_log("read:Leaved")

            return ret


# import heapq
# class MinHeapBuffer:
#     def __init__(self, size):
#         self.size = size
#         self.buffer = []
#
#     def write(self, data):
#         heapq.heappush(self.buffer, data)
#         if len(self.buffer) > self.size:
#             heapq.heappop(self.buffer)
#
#     def read(self):
#         return heapq.heappop(self.buffer)
#
#     def empty(self):
#         return len(self.buffer) == 0

