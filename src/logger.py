import time


LOG_FILE = 'log/log.txt'


class Logger:
    @staticmethod
    def log(string):
        time_str = time.strftime("%d.%m.%Y %H:%M:%S | ", time.localtime())
        line = time_str + string
        print(line)

        # TODO add date to file and check if log folder + file exists
        with open(LOG_FILE, 'a+') as log_file:
            log_file.write(line + '\n')
