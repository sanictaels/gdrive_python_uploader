# gdrive_python_uploader
Hi frenz, simple script to upload archive files to google drive.
Script should automatically set file name as DD_MMM_YYYY.mp4. 
If there's any changes..GG.

## 1-time setup of google OAuth consent
https://developers.google.com/drive/api/quickstart/go


1. Set up Oauth2 on google APIs
	- go to https://console.cloud.google.com/apis/
		- Under Enable APIs, ensure that google drive and youtube have been selected
	- Go to OAuth Consent Screen
		- Ensure these scopes are enabled 
			- /auth/drive.appdate
			- /auth/drive.file
			- /auth/youtube.upload
	- Go to Credentials
		- Create OAuth 2.0 Client IDs
		- Download the JSON file and store it in same folder as the python script. For now, this JSON should be renamed as "test.json"
		
1. Run python script and OAuth authenticate for the first time
	- For some reason, I dont know why we need to auth twice. Once for Drive, once for youtube
1. Enter Sermon Title, Verse, Preacher's name (without Pastor)
1. Watch upload go BRRRRRRRRRRRRRRR


pip install -r requirements.txt 

python upload.py 
