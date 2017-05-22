class DriveInterfaceException(BaseException):
    pass


class DriveInterface:
    QUERY_PHOTO_UPLOAD_FOLDER = 'name=\'FOTO UPLOAD\' and ' \
                                    'mimeType=\'application/vnd.google-apps.folder\''

    QUERY_SUBFOLDER = '\'{0}\' in parents and ' \
                           'mimeType=\'application/vnd.google-apps.folder\' and ' \
                           'trashed=false'

    QUERY_MEDIA_FILES = '\'{0}\' in parents and ' \
                        '(mimeType contains \'image/\' or mimeType contains \'video/\')'

    def check_folder_content(self, drive_service):
        page_token = None
        response = drive_service.files().list(q=self.QUERY_PHOTO_UPLOAD_FOLDER, spaces='drive', pageToken=page_token).execute()

        file = response.get('files', [])

        if len(file) > 1:
            raise DriveInterfaceException("Error: More than one photo upload folder!")

        file = file[0]

        print('Name: {0}, ID: {1}\n'.format(file.get('name'), file.get('id')))

        page_token = None
        response = drive_service.files().list(q=self.QUERY_SUBFOLDER.format(file.get('id')),
                                              spaces='drive',
                                              pageToken=page_token)\
            .execute()

        year_folders = response.get('files', [])

        print("Years")
        for year_folder in year_folders:
            print('Name: {0}, ID: {1}'.format(year_folder.get('name'), year_folder.get('id')))

            print('\nMedia files:')
            page_token = None
            while True:
                event_folders_response = drive_service.files().list(q=self.QUERY_SUBFOLDER.format(year_folder.get('id')),
                                                                  spaces='drive',
                                                                  pageToken=page_token)\
                    .execute()

                event_folders = event_folders_response.get('files', [])

                for event_folder in event_folders:
                    print('Name: {0}, ID: {1}'.format(event_folder.get('name'), event_folder.get('id')))

                page_token = event_folders_response.get('nextPageToken', None)
                if page_token is None:
                    break

    def download_files(self, files):
        pass

    def copy_to_folder(self):
        pass
