import time


class Logger:
    @staticmethod
    def log(string):
        time_str = time.strftime("%d.%m.%Y %H:%M:%S | ", time.localtime())
        print(time_str + string)
