class DriveDownloaderException(BaseException):
    def __init__(self, msg):
        self._msg = msg

    def __str__(self):
        return str(self._msg)