class DriveInterfaceException(BaseException):
    pass


class DriveInterface:
    QUERY_PHOTO_UPLOAD_FOLDER = 'name=\'{0}\' and ' \
                                'mimeType=\'application/vnd.google-apps.folder\''

    QUERY_SUBFOLDER = '\'{0}\' in parents and ' \
                      'mimeType=\'application/vnd.google-apps.folder\' and ' \
                      'trashed=false'

    QUERY_MEDIA_FILES = '\'{0}\' in parents and ' \
                        '(mimeType contains \'image/\' or mimeType contains \'video/\')'

    def __init__(self, root_folder):
        self._root_folder = root_folder

    def check_folder_content(self, drive_service):
        complete_structure = {'content': []}

        upload_folder = self.load_upload_folder(drive_service)
        upload_folder['content'] = []
        complete_structure['content'].append(upload_folder)

        year_folders = self.load_year_folders(drive_service, upload_folder)

        for i, year_folder in enumerate(year_folders):
            year_folder['content'] = []
            complete_structure['content'][0]['content'].append(year_folder)

            event_page_token = None
            while True:
                event_folders, event_folders_response = self.load_event_folders(drive_service, event_page_token,
                                                                                year_folder)

                for j, event_folder in enumerate(event_folders):
                    event_folder['content'] = []
                    complete_structure['content'][0]['content'][i]['content'].append(event_folder)

                    media_files = self.load_media_files(drive_service, event_folder)
                    complete_structure['content'][0]['content'][i]['content'][j]['content'] = media_files

                event_page_token = event_folders_response.get('nextPageToken', None)
                if event_page_token is None:
                    break

        return complete_structure

    def load_event_folders(self, drive_service, event_page_token, year_folder):
        event_folders_response = drive_service.files().list(
            q=self.QUERY_SUBFOLDER.format(year_folder['id']),
            spaces='drive',
            fields='nextPageToken, files(id, name)',
            pageToken=event_page_token) \
            .execute()
        event_folders = event_folders_response.get('files', [])
        return event_folders, event_folders_response

    def load_media_files(self, drive_service, event_folder):
        media_page_token = None
        media_files = []
        while True:
            media_response = drive_service.files().list(
                q=self.QUERY_MEDIA_FILES.format(event_folder['id']),
                spaces='drive',
                pageToken=media_page_token) \
                .execute()

            media_files += media_response.get('files', [])

            media_page_token = media_response.get('nextPageToken', None)
            if media_page_token is None:
                break

        return media_files

    def load_year_folders(self, drive_service, upload_folder):
        year_folder_response = drive_service.files().list(q=self.QUERY_SUBFOLDER.format(upload_folder['id']),
                                                          spaces='drive') \
            .execute()
        year_folders = year_folder_response.get('files', [])
        return year_folders

    def load_upload_folder(self, drive_service):
        upload_folder_response = drive_service.files().list(q=self.QUERY_PHOTO_UPLOAD_FOLDER.format(self._root_folder),
                                                            spaces='drive')\
            .execute()
        upload_folder = upload_folder_response.get('files', [])

        if len(upload_folder) > 1:
            raise DriveInterfaceException("Error: More than one photo upload folder!")

        upload_folder = upload_folder[0]
        return upload_folder

    def download_files(self, files):
        pass

    def copy_to_folder(self):
        pass
