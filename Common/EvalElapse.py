
class EvalElapse:
    def __init__(self, ignore_first_over_time=1., float_format="{:.3f}"):
        self.index = 0
        self.elapse_min = None
        self.elapse_max = None
        self.elapse_avg = None
        
        self.ignore_first_over_time = ignore_first_over_time
        self.float_format = float_format
        self.elapse_format = "min:{} sec, max:{} sec, avg:{} sec".format(float_format, float_format, float_format)

    def add(self, elapse):
        # 첫번째는 느릴수 있기 때문에 속도측정에서 제외
        if self.index == 0 and self.ignore_first_over_time and elapse > float(self.ignore_first_over_time):
            self.ignore_first_over_time = None
            return

        self.index += 1

        if not self.elapse_min or self.elapse_min > elapse:
            self.elapse_min = elapse

        if not self.elapse_max or self.elapse_max < elapse:
            self.elapse_max = elapse

        if not self.elapse_avg:
            self.elapse_avg = elapse
        else:
            self.elapse_avg = (self.elapse_avg * (self.index - 1) + elapse) / self.index

    def set_fail(self):
        self.index = 0
        self.elapse_min = None
        self.elapse_max = None
        self.elapse_avg = None

    def avg_str(self):
        if not self.elapse_avg:
            return "Nan"
        return self.float_format.format(self.elapse_avg)

    def __str__(self):
        if self.index == 0:
            return "Nan"
        return self.elapse_format.format(self.elapse_min, self.elapse_max, self.elapse_avg)
