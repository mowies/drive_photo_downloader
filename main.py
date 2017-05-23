import httplib2
import os
import argparse
import sched

from apiclient import discovery
from oauth2client import client
from oauth2client import tools
from oauth2client.file import Storage

from drive_interface import DriveInterface
from disk_interface import DiskInterface


# If modifying these scopes, delete your previously saved credentials
# at ~/.credentials/drive-python-quickstart.json
SCOPES = ["https://www.googleapis.com/auth/drive"]
CLIENT_SECRET_FILE = 'data/client_secret.json'
APPLICATION_NAME = 'Drive API Python Quickstart'

DRIVE_ROOT_FOLDER = 'FOTO UPLOAD'
LOCAL_ROOT_FOLDER = 'DESTINATION/'


class Main:
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
        credential_path = os.path.join(credential_dir,
                                       'drive-python-quickstart.json')

        store = Storage(credential_path)
        credentials = store.get()
        if not credentials or credentials.invalid:
            flow = client.flow_from_clientsecrets(CLIENT_SECRET_FILE, SCOPES)
            flow.user_agent = APPLICATION_NAME
            credentials = tools.run_flow(flow, store, flags)
            print('Storing credentials to ' + credential_path)
        return credentials

    def main(self, root_folder):
        """Shows basic usage of the Google Drive API.
    
        Creates a Google Drive API service object and read from drive and saves to disk.
        """
        flags = argparse.ArgumentParser(parents=[tools.argparser]).parse_args()
        credentials = self.get_credentials(flags)
        http = credentials.authorize(httplib2.Http())
        service = discovery.build('drive', 'v3', http=http)

        drive_interface = DriveInterface(root_folder, service)
        disk_interface = DiskInterface(LOCAL_ROOT_FOLDER, drive_interface)
        file_structure = drive_interface.check_folder_content()
        self.pretty_print(file_structure)

        disk_interface.write_all(file_structure)

        # for file in file_structure['content'][0]['content'][0]['content'][0]['content']:
        #     file_stream = drive_interface.download_file(file)
        #     disk_interface.write_image_file(file_stream, file['name'])

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
    main_class.main(DRIVE_ROOT_FOLDER)
