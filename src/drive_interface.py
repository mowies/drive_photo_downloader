import io
from googleapiclient.http import MediaIoBaseDownload


class DriveInterfaceException(BaseException):
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

    def __init__(self, root_folder, drive_service):
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
            fields='nextPageToken, files(id, name)',
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
                pageToken=media_page_token) \
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
            raise DriveInterfaceException("Error: More than one photo upload folder!")

        upload_folder = upload_folder[0]
        return upload_folder

    def download_file(self, file):
        request = self._drive_service.files().get_media(fileId=file['id'])
        stream = io.BytesIO()
        downloader = MediaIoBaseDownload(stream, request)
        done = False
        while not done:
            status, done = downloader.next_chunk()
            print('File: {0} | {1}%'.format(file['name'], int(status.progress() * 100)))

        return stream
