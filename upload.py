from __future__ import print_function
import sys
import os
import httplib2
import random
import time
import google.auth
from datetime import date
from pathlib import Path
from tqdm import tqdm
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaFileUpload
from google_auth_oauthlib.flow import InstalledAppFlow
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from oauth2client.client import flow_from_clientsecrets
from oauth2client.file import Storage
from oauth2client.tools import argparser, run_flow

SCOPES = ['https://www.googleapis.com/auth/drive','https://www.googleapis.com/auth/youtube.upload']
folder = ''
httplib2.RETRIES = 1

# Maximum number of times to retry before giving up.
MAX_RETRIES = 10

# Always retry when these exceptions are raised.
RETRIABLE_EXCEPTIONS = (httplib2.HttpLib2Error,)

# Always retry when an apiclient.errors.HttpError with one of these status
# codes is raised.
RETRIABLE_STATUS_CODES = [500, 502, 503, 504]
CLIENT_SECRETS_FILE = "test.json"
YOUTUBE_API_SERVICE_NAME = "youtube"
YOUTUBE_API_VERSION = "v3"

VALID_PRIVACY_STATUSES = ("public", "private", "unlisted")

def upload_basic(Filename):
    filename = Filename
    filesize= os.stat(Filename).st_size
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
        filename_noext = Path(filename).stem
        file_metadata = {'name': filename_noext}
        media = MediaFileUpload(filename,chunksize=1024*1024,mimetype='video/mp4', resumable=True)
        media.stream()
        # pylint: disable=maybe-no-member
        file = service.files().create(body=file_metadata, media_body=media,fields='id')
        #adding upload progress bar
        response = None
        last_progress = 0
        pbar = tqdm(total=100, desc= "Uploading file :" + filename_noext, unit='KB')
        print ("File selected :" + filename)
#        print ("Total size :" + str(int(filesize/1024)) + "MB")
        while response is None:
            status, response = file.next_chunk()
            if status:
                #print ("Uploaded %d%%." % int(status.progress() * 100))
                p = status.progress() * 100
                dp = p - last_progress
                pbar.update(dp)
                last_progress = p
        pbar.update(100-last_progress)
        #done    
        print(F'File ID: {response.get("id")}')

    except HttpError as error:
        print(F'An error occurred: {error}')
        file = None

    return response.get('id')

#youtube part

def get_authenticated_service(args):
  flow = flow_from_clientsecrets(CLIENT_SECRETS_FILE,
    scope=SCOPES)

  storage = Storage("%s-oauth2.json" % sys.argv[0])
  credentials = storage.get()

  if credentials is None or credentials.invalid:
    credentials = run_flow(flow, storage, args)

  return build(YOUTUBE_API_SERVICE_NAME, YOUTUBE_API_VERSION,
    http=credentials.authorize(httplib2.Http()))

def initialize_upload(youtube, options):
  tags = None
  if options.keywords:
    tags = options.keywords.split(",")

  body=dict(
    snippet=dict(
      title=options.title,
      description=options.description,
      tags=tags,
      categoryId=options.category
    ),
    status=dict(
      privacyStatus=options.privacyStatus
    )
  )

  # Call the API's videos.insert method to create and upload the video.
  insert_request = youtube.videos().insert(
    part=",".join(body.keys()),
    body=body,
    # The chunksize parameter specifies the size of each chunk of data, in
    # bytes, that will be uploaded at a time. Set a higher value for
    # reliable connections as fewer chunks lead to faster uploads. Set a lower
    # value for better recovery on less reliable connections.
    #
    # Setting "chunksize" equal to -1 in the code below means that the entire
    # file will be uploaded in a single HTTP request. (If the upload fails,
    # it will still be retried where it left off.) This is usually a best
    # practice, but if you're using Python older than 2.6 or if you're
    # running on App Engine, you should set the chunksize to something like
    # 1024 * 1024 (1 megabyte).
    media_body=MediaFileUpload(options.file, chunksize=-1, resumable=True)
  )

  id=resumable_upload(insert_request)
  return id
# This method implements an exponential backoff strategy to resume a
# failed upload.
def resumable_upload(insert_request):
  response = None
  error = None
  retry = 0
  while response is None:
    try:
      print ("Uploading file...")
      status, response = insert_request.next_chunk()
      if response is not None:
        if 'id' in response:
          print ("Video id '%s' was successfully uploaded." % response['id'])
        else:
          exit("The upload failed with an unexpected response: %s" % response)
    except HttpError as e:
      if e.resp.status in RETRIABLE_STATUS_CODES:
        error = "A retriable HTTP error %d occurred:\n%s" % (e.resp.status,
                                                             e.content)
      else:
        raise
    except RETRIABLE_EXCEPTIONS as e:
      error = "A retriable error occurred: %s" % e

    if error is not None:
      print (error)
      retry += 1
      if retry > MAX_RETRIES:
        exit("No longer attempting to retry.")

      max_sleep = 2 ** retry
      sleep_seconds = random.random() * max_sleep
      print ("Sleeping %f seconds and then retrying..." % sleep_seconds)
      time.sleep(sleep_seconds)
    return response.get('id')
    
if __name__ == '__main__':
    title = input("Enter the Title: ")
    verse = input("Enter the Verse: ")
    p_name = input("Enter the Preacher's name: ")
    today = date.today()
    fname = today.strftime("%d_%b_%Y.mp4").lower()
    print("Title : " + title + "\nVerse : " + verse + "\nPreacher : Pastor " + p_name )
    input("Press any key to confirm")
    gdriveID = upload_basic(fname)
    argparser.add_argument("--file", default=fname)
    argparser.add_argument("--title", help="Video title", default=title)
    argparser.add_argument("--description", help="Video description",
    default="Test Description")
    argparser.add_argument("--category", default="22",
    help="Numeric video category. " +
      "See https://developers.google.com/youtube/v3/docs/videoCategories/list")
    argparser.add_argument("--keywords", help="Video keywords, comma separated",
    default="")
    argparser.add_argument("--privacyStatus", choices=VALID_PRIVACY_STATUSES,
    default=VALID_PRIVACY_STATUSES[2], help="Video privacy status.")
    args = argparser.parse_args()
    youtube = get_authenticated_service(args)
    try:
        utub_id = initialize_upload(youtube, args)
    except HttpError as e:
        print ("An HTTP error %d occurred:\n%s" % (e.resp.status, e.content))
    print ("Youtube ID : " + utub_id)
    print ("Gdrive ID : " + gdriveID)
    print ("Youtube Thumbnail : https://img.youtube.com/vi/"+ utub_id +"/default.jpg" )