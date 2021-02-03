

class MinMaxHeapBuffer:
    def __init__(self, size, key_lambda=None, min_heap=True):
        self.key_lambda = key_lambda
        self.min_heap = min_heap
        self.buffer = [None, ] * size
        self.end = 0

    def find(self, key):
        for idx in range(self.end):
            value = self.buffer[idx]
            if self.key_lambda is not None:
                value = self.key_lambda(value)
            if value == key:
                return self.buffer[idx]
        return None

    def compare(self, a_idx, b_idx):
        left = self.buffer[a_idx]
        right = self.buffer[b_idx]

        if self.key_lambda is not None:
            left = self.key_lambda(left)
            right = self.key_lambda(right)

        cmp = left < right
        if not self.min_heap:
            cmp = not cmp
        return cmp

    def write(self, data):
        if self.end >= len(self.buffer):
            self.read()

        self.buffer[self.end] = data
        self.end += 1

        child = self.end
        parent = int(child / 2)
        while parent > 0:
            if self.compare(parent-1, child-1):
                break

            self.buffer[parent-1], self.buffer[child-1] = self.buffer[child-1], self.buffer[parent-1]

            child = parent
            parent = int(child / 2)

    def read(self):
        if self.end == 0:
            return None

        ret = self.buffer[0]

        self.end -= 1
        if self.end == 0:
            return ret

        self.buffer[0] = self.buffer[self.end]

        parent = 1
        child = parent * 2

        while child <= self.end:
            if child + 1 <= self.end:     # find min child if min heap else max child when having right child
                if not self.compare(child-1, child):
                    child += 1

            if self.compare(parent-1, child-1):
                break

            self.buffer[parent-1], self.buffer[child-1] = self.buffer[child-1], self.buffer[parent-1]
            parent = child
            child = parent * 2

        return ret

    def empty(self):
        return self.end == 0

    def full(self):
        return self.end == len(self.buffer)

    def clear(self):
        self.buffer = [None, ] * len(self.buffer)
        self.end = 0


if __name__ == '__main__':  # 테스트 용
    class TestData:
        def __init__(self, frame_no, frame):
            self.frame_no = frame_no
            self.frame = frame

        def __str__(self):
            return '{} : {}'.format(self.frame_no, self.frame)

    test = [9, 4, 6, 2, 7, 10]

    heap_buffer = MinMaxHeapBuffer(20, key_lambda=(lambda x: x.frame_no))
    for idx, v in enumerate(test):
        heap_buffer.write(TestData(v, idx))

    while not heap_buffer.empty():
        print([str(v) for v in heap_buffer.buffer if v is not None])
        v = heap_buffer.read()
        print(str(v))
