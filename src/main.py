import os
import argparse
import json
import ntpath
import time
import httplib2
import sys

from collections import OrderedDict
from apiclient import discovery
from oauth2client import client
from oauth2client import tools
from oauth2client.file import Storage

from disk_interface import DiskInterface
from drive_interface import DriveInterface
from logger import Logger
from downloader_exception import DriveDownloaderException

# If modifying these scopes, delete your previously saved credentials
# at ~/.credentials/credentials.json
SCOPES = ["https://www.googleapis.com/auth/drive"]
APPLICATION_NAME = 'Google Drive Automatic Media Downloader'

CONFIG_PATH = 'data/config.json'
CONFIG_DRIVE = 'drive_root_folder'
CONFIG_LOCAL = 'local_root_folder'
CONFIG_CLIENT_SECRET = 'client_secret_path'
CONFIG_BACKUP_INTERVAL = 'backup_interval'
CONFIG_DELETE_METHOD = 'delete_method'


class Main:
    def __init__(self):
        self._logger = Logger()
        self._drive_root_folder = ''
        self._local_root_folder = ''
        self._client_secret_path = ''
        self._backup_interval = 0.0
        self._delete_method = 0  # 0 for trash, 1 for delete

    @property
    def logger(self):
        return self._logger

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
            self._logger.log('Storing credentials to ' + credential_path)
        return credentials

    def main(self):
        """Shows basic usage of the Google Drive API.
    
        Creates a Google Drive API service object and read from drive and saves to disk.
        """
        flags = argparse.ArgumentParser(parents=[tools.argparser]).parse_args()
        credentials = self.get_credentials(flags)
        http = credentials.authorize(httplib2.Http())
        service = discovery.build('drive', 'v3', http=http)

        drive_interface = DriveInterface(self._logger, self._drive_root_folder, service)
        disk_interface = DiskInterface(self._logger, self._local_root_folder, self._delete_method, drive_interface)

        self._logger.log('Starting backup loop...')
        self.loop(drive_interface, disk_interface)

    def loop(self, drive_interface, disk_interface):
        start_time = time.time()

        while True:
            self._logger.log('Updating file structure...')
            file_structure = drive_interface.check_folder_content()
            # self.pretty_print(file_structure)

            self._logger.log('Starting to download new media...')
            disk_interface.copy_to_disk(file_structure)
            self._logger.log('Media download done.')

            self._logger.log('Going to sleep for 5 minutes...\n')
            time.sleep(self._backup_interval - ((time.time() - start_time) % self._backup_interval))

    def get_config(self):
        try:
            with open(CONFIG_PATH, 'r') as config_file:
                config = json.load(config_file)
        except FileNotFoundError:
            config_dict = OrderedDict()
            config_dict[CONFIG_DRIVE] = "please enter only folder"
            config_dict[CONFIG_LOCAL] = "please enter the absolute path"
            config_dict[CONFIG_CLIENT_SECRET] = "please enter relative path to client secret"
            config_dict[CONFIG_BACKUP_INTERVAL] = "please enter backup interval in seconds"
            config_dict[CONFIG_DELETE_METHOD] = "trash"

            config_path = "".join([folder for folder in ntpath.split(CONFIG_PATH)[0:-1]])
            os.makedirs(config_path, exist_ok=True)

            with open(CONFIG_PATH, 'w') as config_file:
                json.dump(config_dict, config_file)

                self._logger.log('This is probably the first start of this script. '
                                 'Please fill in the configuration file (data/config.json)')
            return False

        if not os.path.isabs(config[CONFIG_LOCAL]):
            self._logger.log('Please enter the ABSOLUTE path for the local root folder in the configuration file.')
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
            raise DriveDownloaderException('Delete method configuration not correctly set. '
                                           'Please set to \"trash\" (move to trash) or \"delete\" (delete permanently)')
        return True

    def pretty_print(self, folder_structure):
        self._logger.log("Complete folder structure:")
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
    try:
        main_class = Main()

        config_done = main_class.get_config()

        if config_done:
            main_class.main()
    except (Exception, BaseException) as e:
        if main_class.logger is not None:
            main_class.logger.log('Error: {0}'.format(str(e)))
    except:
        msg = sys.exc_info()[1]
        time_str = time.strftime("%d.%m.%Y %H:%M:%S |", time.localtime())
        with open("log/ERROR.txt", "w") as f:
            f.write('{0} Error: {1}'.format(time_str, msg))
