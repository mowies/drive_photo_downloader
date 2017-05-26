import os
import argparse
import json
import ntpath
import time

import httplib2
from apiclient import discovery
from oauth2client import client
from oauth2client import tools
from oauth2client.file import Storage

from src.disk_interface import DiskInterface
from src.drive_interface import DriveInterface

# If modifying these scopes, delete your previously saved credentials
# at ~/.credentials/credentials.json
SCOPES = ["https://www.googleapis.com/auth/drive"]
APPLICATION_NAME = 'Drive API Python Quickstart'

CONFIG_PATH = 'data/config.json'
CONFIG_DRIVE = 'drive_root_folder'
CONFIG_LOCAL = 'local_root_folder'
CONFIG_CLIENT_SECRET = 'client_secret_path'
CONFIG_BACKUP_INTERVAL = 'backup_interval'
CONFIG_DELETE_METHOD = 'delete_method'


class DriveDownloaderException(BaseException):
    pass


class Main:
    def __init__(self):
        self._drive_root_folder = ''
        self._local_root_folder = ''
        self._client_secret_path = ''
        self._backup_interval = 0.0
        self._delete_method = 0  # 0 for trash, 1 for delete

    def get_credentials(self, flags):
        """Gets valid user credentials from storage.
    
        If nothing has been stored, or if the stored credentials are invalid,
        the OAuth2 flow is completed to obtain the new credentials.
    
        Returns:
            Credentials, the obtained credential.
        """
        home_dir = os.path.expanduser('~')
        credential_dir = os.path.join(home_dir, '.credentials')
        if not os.path.exists(credential_dir):
            os.makedirs(credential_dir)
        credential_path = os.path.join(credential_dir, 'credentials.json')

        store = Storage(credential_path)
        credentials = store.get()
        if not credentials or credentials.invalid:
            flow = client.flow_from_clientsecrets(self._client_secret_path, SCOPES)
            flow.user_agent = APPLICATION_NAME
            credentials = tools.run_flow(flow, store, flags)
            print('Storing credentials to ' + credential_path)
        return credentials

    def main(self):
        """Shows basic usage of the Google Drive API.
    
        Creates a Google Drive API service object and read from drive and saves to disk.
        """
        flags = argparse.ArgumentParser(parents=[tools.argparser]).parse_args()
        credentials = self.get_credentials(flags)
        http = credentials.authorize(httplib2.Http())
        service = discovery.build('drive', 'v3', http=http)

        drive_interface = DriveInterface(self._drive_root_folder, service)
        disk_interface = DiskInterface(self._local_root_folder, self._delete_method, drive_interface)

        print('Starting backup loop...')
        self.loop(drive_interface, disk_interface)

    def loop(self, drive_interface, disk_interface):
        start_time = time.time()

        while True:
            print('Updating file structure... (Time: {0})'.format(str(time.strftime("%d.%m.%Y - %H:%M:%S", time.localtime()))))
            file_structure = drive_interface.check_folder_content()
            # self.pretty_print(file_structure)

            print('Starting to download new media...')
            disk_interface.copy_to_disk(file_structure)

            print('Going to sleep for 5 minutes...\n')
            time.sleep(self._backup_interval - ((time.time() - start_time) % self._backup_interval))

    def get_config(self):
        try:
            with open(CONFIG_PATH, 'r') as config_file:
                config = json.load(config_file)
        except FileNotFoundError:
            config_dict = {
                CONFIG_DRIVE: "please enter only folder",
                CONFIG_LOCAL: "please enter the absolute path",
                CONFIG_CLIENT_SECRET: "please enter relative path to client secret",
                CONFIG_BACKUP_INTERVAL: "please enter backup interval in seconds",
                CONFIG_DELETE_METHOD: "trash"
            }

            config_path = "".join([folder for folder in ntpath.split(CONFIG_PATH)[0:-1]])
            os.makedirs(config_path, exist_ok=True)

            with open(CONFIG_PATH, 'w') as config_file:
                json.dump(config_dict, config_file)

            print('This is probably the first start of this script. '
                  'Please fill in the configuration file (data/config.json)')
            return False

        if not os.path.isabs(config[CONFIG_LOCAL]):
            print('Please enter the ABSOLUTE path for the local root folder in the configuration file.')
            return False

        self._drive_root_folder = config[CONFIG_DRIVE]
        self._local_root_folder = config[CONFIG_LOCAL]
        self._client_secret_path = config[CONFIG_CLIENT_SECRET]
        self._backup_interval = float(config[CONFIG_BACKUP_INTERVAL])

        if config[CONFIG_DELETE_METHOD] == 'trash':
            self._delete_method = 0
        elif config[CONFIG_DELETE_METHOD] == 'delete':
            self._delete_method = 1
        else:
            raise DriveDownloaderException('Delete method configuration not correctly set.\n'
                                           'Please set to \"trash\" (move to trash) or \"delete\" (delete permanently)')
        return True

    def pretty_print(self, folder_structure):
        print("Complete folder structure:")
        self.pretty_print_aux(0, folder_structure)

    def pretty_print_aux(self, level, obj_to_print):
        indent = ""
        for i in range(level):
            indent += "   "

        try:
            for item in obj_to_print['content']:
                print(indent, end='')
                print("|- ", end='')
                print(item['name'])
                self.pretty_print_aux(level + 1, item)
        except KeyError:
            return

if __name__ == '__main__':
    main_class = Main()

    config_done = main_class.get_config()

    if config_done:
        main_class.main()
