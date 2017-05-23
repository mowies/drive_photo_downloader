import os

from PIL import Image


class DiskInterfaceException(BaseException):
    pass


class DiskInterface:
    def __init__(self, root_path, drive_interface):
        self._root_path = root_path
        self._drive_interface = drive_interface

    def write_all(self, structure):
        root_folder = structure['content'][0]
        for year_folder in root_folder['content']:
            for event_folder in year_folder['content']:
                for img_file in event_folder['content']:
                    rel_path = os.path.join(year_folder['name'], event_folder['name'])
                    complete_path = os.path.join(rel_path, img_file['name'])
                    img_stream = self._drive_interface.download_file(img_file)
                    self.create_folder(rel_path)
                    self.write_image_file(img_stream, complete_path)

    def create_folder(self, rel_path):
        path = os.path.join(self._root_path, rel_path)
        os.makedirs(path, exist_ok=True)

    def write_image_file(self, img_stream, rel_file_path):
        path = os.path.join(self._root_path, rel_file_path)
        img = Image.open(img_stream)
        img.save(path)
