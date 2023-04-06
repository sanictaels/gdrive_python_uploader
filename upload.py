from __future__ import print_function
import sys
import os
import google.auth
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaFileUpload
from google_auth_oauthlib.flow import InstalledAppFlow
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request

SCOPES = ['https://www.googleapis.com/auth/drive']
folder = ''

def upload_basic(Filename):
    filename = Filename
    creds = None
    # The file token.json stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'test.json', SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open('token.json', 'w') as token:
            token.write(creds.to_json())

    try:
        # create drive api client
        service = build('drive', 'v3', credentials=creds)

        file_metadata = {'name': filename}
        media = MediaFileUpload(filename,chunksize=1024*1024,mimetype='video/mp4', resumable=True)
        media.stream()
        # pylint: disable=maybe-no-member
        file = service.files().create(body=file_metadata, media_body=media,fields='id')
        #adding upload progress bar
        response = None
        while response is None:
            status, response = file.next_chunk()
        if status:
            print ("Uploaded %d%%." % int(status.progress() * 100))
        #done    
        print(F'File ID: {response.get("id")}')

    except HttpError as error:
        print(F'An error occurred: {error}')
        file = None

    return response.get('id')


if __name__ == '__main__':
    if len(sys.argv) == 2:
        upload_basic(sys.argv[1])
    else:
        print("Please enter one argument.")
        