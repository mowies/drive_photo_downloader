import time
import os


LOG_PATH = 'log/'


class Logger:
    def __init__(self):
        os.makedirs(LOG_PATH, exist_ok=True)
        self._log_path = os.path.join(LOG_PATH, time.strftime("log_%d_%m_%Y.txt"))
        self.log('Starting Logger...')

    def log(self, string):
        time_str = time.strftime("%d.%m.%Y %H:%M:%S | ", time.localtime())
        line = time_str + string
        print(line)

        with open(self._log_path, 'a+') as log_file:
            log_file.write(line + '\n')
