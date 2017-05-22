import httplib2
import os
import argparse
import sched

from apiclient import discovery
from oauth2client import client
from oauth2client import tools
from oauth2client.file import Storage

from drive_interface import DriveInterface


# If modifying these scopes, delete your previously saved credentials
# at ~/.credentials/drive-python-quickstart.json
SCOPES = ["https://www.googleapis.com/auth/drive"]
CLIENT_SECRET_FILE = 'data/client_secret.json'
APPLICATION_NAME = 'Drive API Python Quickstart'


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
            if flags:
                credentials = tools.run_flow(flow, store, flags)
            else:  # Needed only for compatibility with Python 2.6
                credentials = tools.run(flow, store)
            print('Storing credentials to ' + credential_path)
        return credentials

    def main(self):
        """Shows basic usage of the Google Drive API.
    
        Creates a Google Drive API service object and outputs the names and IDs
        for up to 10 files.
        """
        flags = argparse.ArgumentParser(parents=[tools.argparser]).parse_args()
        credentials = self.get_credentials(flags)
        http = credentials.authorize(httplib2.Http())
        service = discovery.build('drive', 'v3', http=http)

        # results = service.files().list(pageSize=10, fields="nextPageToken, files(id, name)").execute()
        # items = results.get('files', [])
        # if not items:
        #     print('No files found.')
        # else:
        #     print('Files:')
        #     for item in items:
        #         print('{0} ({1})'.format(item['name'], item['id']))

        drive_interface = DriveInterface()
        file_structure = drive_interface.check_folder_content(service)
        self.pretty_print(file_structure)

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
    main_class.main()
