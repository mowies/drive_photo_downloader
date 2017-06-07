import io

from googleapiclient.http import MediaIoBaseDownload

from downloader_exception import DriveDownloaderException


class DriveInterfaceException(DriveDownloaderException):
    pass


class DriveInterface:
    QUERY_PHOTO_UPLOAD_FOLDER = 'name=\'{0}\' and ' \
                                'mimeType=\'application/vnd.google-apps.folder\''

    QUERY_SUBFOLDER = '\'{0}\' in parents and ' \
                      'mimeType=\'application/vnd.google-apps.folder\' and ' \
                      'trashed=false'

    QUERY_IMAGE_FILES = '\'{0}\' in parents and ' \
                        'mimeType contains \'image/\' and ' \
                        'trashed=false'

    QUERY_VIDEO_FILES = '\'{0}\' in parents and ' \
                        'mimeType contains \'video/\' and ' \
                        'trashed=false'

    QUERY_FOLDER_STATE_FILE = 'name contains \' FOTOS.txt\' and ' \
                              '\'{0}\' in parents and ' \
                              'mimeType != \'application/vnd.google-apps.folder\' and ' \
                              'trashed=false'

    MEDIA_FILE_FIELDS = 'files(id,mimeType,name,parents,trashed),nextPageToken'
    EVENT_FOLDER_FIELDS = 'nextPageToken, files(id, name)'

    def __init__(self, logger, root_folder, drive_service):
        self._logger = logger
        self._root_folder = root_folder
        self._drive_service = drive_service

    def check_folder_content(self):
        complete_structure = {'content': []}

        upload_folder = self.load_upload_folder()
        upload_folder['content'] = []
        complete_structure['content'].append(upload_folder)

        year_folders = self.load_year_folders(upload_folder)

        for i, year_folder in enumerate(year_folders):
            year_folder['content'] = []
            complete_structure['content'][0]['content'].append(year_folder)

            event_page_token = None
            while True:
                event_folders, event_folders_response = self.load_event_folders(event_page_token, year_folder)

                for j, event_folder in enumerate(event_folders):
                    event_folder['content'] = []
                    complete_structure['content'][0]['content'][i]['content'].append(event_folder)

                    media_files = self.load_media_files(event_folder)
                    complete_structure['content'][0]['content'][i]['content'][j]['content'] = media_files

                event_page_token = event_folders_response.get('nextPageToken', None)
                if event_page_token is None:
                    break

        return complete_structure

    def load_event_folders(self, event_page_token, year_folder):
        event_folders_response = self._drive_service.files().list(
            q=self.QUERY_SUBFOLDER.format(year_folder['id']),
            spaces='drive',
            fields=self.EVENT_FOLDER_FIELDS,
            pageToken=event_page_token) \
            .execute()
        event_folders = event_folders_response.get('files', [])
        return event_folders, event_folders_response

    def load_media_files(self, event_folder):
        media_page_token = None
        media_files = []
        while True:
            media_response = self._drive_service.files().list(
                q=self.QUERY_IMAGE_FILES.format(event_folder['id']),
                spaces='drive',
                pageToken=media_page_token,
                fields=self.MEDIA_FILE_FIELDS) \
                .execute()

            media_files += media_response.get('files', [])

            media_page_token = media_response.get('nextPageToken', None)
            if media_page_token is None:
                break

        return media_files

    def load_year_folders(self, upload_folder):
        year_folder_response = self._drive_service.files().list(q=self.QUERY_SUBFOLDER.format(upload_folder['id']),
                                                                spaces='drive') \
            .execute()
        year_folders = year_folder_response.get('files', [])
        return year_folders

    def load_upload_folder(self):
        upload_folder_response = self._drive_service.files().list(q=self.QUERY_PHOTO_UPLOAD_FOLDER.format(self._root_folder),
                                                                  spaces='drive')\
            .execute()
        upload_folder = upload_folder_response.get('files', [])

        if len(upload_folder) > 1:
            raise DriveInterfaceException('More than one photo upload folder!')

        upload_folder = upload_folder[0]
        return upload_folder

    def download_file(self, file):
        request = self._drive_service.files().get_media(fileId=file['id'])
        stream = io.BytesIO()
        downloader = MediaIoBaseDownload(stream, request)
        done = False
        while not done:
            status, done = downloader.next_chunk()
            self._logger.log('File: {0} | {1}%'.format(file['name'], int(status.progress() * 100)))

        return stream

    def trash_file(self, file):
        metadata = {
            'trashed': True
        }
        self._drive_service.files().update(fileId=file['id'], body=metadata).execute()

    def delete_file(self, file):
        self._drive_service.files().delete(fileId=file['id']).execute()

    def update_folder_state_file(self, folder, file_count):
        new_filename = {'name': '{0} FOTOS.txt'.format(file_count)}
        folder_state_file = self._drive_service.files().list(q=self.QUERY_FOLDER_STATE_FILE.format(folder['id']),
                                                             fields=self.MEDIA_FILE_FIELDS,
                                                             spaces='drive')\
            .execute()

        folder_state_file = folder_state_file.get('files', [])

        if len(folder_state_file) == 1:
            folder_state_file = folder_state_file[0]
            self._drive_service.files().update(fileId=folder_state_file['id'], body=new_filename).execute()
        elif len(folder_state_file) == 0:
            new_filename['parents'] = [folder['id']]
            self._drive_service.files().create(body=new_filename, fields='name,id').execute()
        else:
            for file in folder_state_file:
                self.delete_file(file)
            new_filename['parents'] = [folder['id']]
            self._drive_service.files().create(body=new_filename, fields='name,id').execute()
