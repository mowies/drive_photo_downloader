import os

from PIL import Image

from downloader_exception import DriveDownloaderException


class DiskInterfaceException(DriveDownloaderException):
    pass


class DiskInterface:
    def __init__(self, logger, root_path, delete_method, drive_interface):
        """
        Init.

        :param logger: Logs messages to file
        :type logger: src.logger.Logger
        :param root_path: Path to backup location
        :type root_path: str
        :param delete_method: delete or trash
        :type delete_method: int
        :param drive_interface: Interface to Google Drive
        :type drive_interface: src.drive_interface.DriveInterface
        """
        self._logger = logger
        self._root_path = root_path
        self._drive_interface = drive_interface
        self._delete_method = delete_method

    def copy_to_disk(self, structure):
        root_folder = structure['content'][0]
        for year_folder in root_folder['content']:
            for event_folder in year_folder['content']:
                for img_file in event_folder['content']:
                    rel_path = os.path.join(year_folder['name'], event_folder['name'])
                    complete_path = os.path.join(self._root_path, rel_path, img_file['name'])

                    if not os.path.exists(complete_path):
                        img_stream = self._drive_interface.download_file(img_file)
                        self.create_folder(rel_path)
                        self.write_image_file(img_stream, complete_path)
                        if self._delete_method == 0:
                            self._drive_interface.trash_file(img_file)
                        else:
                            self._drive_interface.delete_file(img_file)
                    else:
                        self._logger.log('File already exists: {0}'.format(img_file['name']))

                    file_count = self.get_image_file_count(os.path.join(self._root_path, rel_path))
                    self._drive_interface.update_folder_state_file(event_folder, file_count)

    def create_folder(self, rel_path):
        self._logger.log('Creating folder: {0}'.format(rel_path))
        path = os.path.join(self._root_path, rel_path)
        os.makedirs(path, exist_ok=True)

    def write_image_file(self, img_stream, rel_file_path):
        path = os.path.join(self._root_path, rel_file_path)
        img = Image.open(img_stream)
        img.save(path)

    @staticmethod
    def get_image_file_count(path):
        files = [file for file in os.listdir(path) if not file.endswith('FOTOS.txt')]
        return len(files)
