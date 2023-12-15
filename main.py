import os
import io
import argparse
import subprocess
import sys

#this isnt pretty, but it works
try:
    try:
        from googleapiclient.http import MediaIoBaseDownload
        from googleapiclient.discovery import build
        from googleapiclient.errors import HttpError

    except ModuleNotFoundError as e:
        a = input("google-api-python-client is not installed, want me to install it? (y/N)").lower()
        if a == "y":
            subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'google-api-python-client'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    try:
        from google.auth.transport.requests import Request
        from google.oauth2.credentials import Credentials
        from google_auth_oauthlib.flow import InstalledAppFlow
    except ModuleNotFoundError as e:
        a = input("google-auth-oauthlib is not installed, want me to install it? (y/N)").lower()
        if a == "y":
            subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'google-auth-oauthlib'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    try:
        import pdf2image
    except ModuleNotFoundError as e:
        a = input("pdf2image is not installed, want me to install it? (y/N)").lower()
        if a == "y":
            subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'pdf2image'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

except subprocess.CalledProcessError as e:
    print("failed to install packages")
    if sys.prefix == sys.base_prefix:
        if os.path.exists('./venv'):
            print(f"youre not running in the virtual environment, try {os.path.abspath('./venv/bin/python')} main.py instead")
        a = input("do you wish to create a virtual environment and run in there? (y/N)")
        if a == "y":
            subprocess.check_call([sys.executable, '-m', 'venv', './venv'], stdout=subprocess.DEVNULL)
            print(f"venv created, you can now run the script as follows: {os.path.abspath('./venv/bin/python')} main.py")
        exit()

    exit()



SCOPES = ['https://www.googleapis.com/auth/drive.readonly'] # scope needed, do not change

parser = argparse.ArgumentParser(
                    prog='SimpleSign',
                    description='Display sign details easily')

parser.add_argument("folder", help="the name of the remote folder")
parser.add_argument("-d", "--delay", default=10, type=int, help="the time each slide is shown for")
parser.add_argument("-b", "--buffer", default="buf/", type=str, help="the local folder pngs are kept")
parser.add_argument("--no-display", dest="noDisplay", action="store_true", help="only update the buffer, do not display")
parser.add_argument("--no-update", dest="noUpdate", action="store_true", help="only display, do not update buffer")


# get authentication details
def auth():
    creds = None

    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)

    #either no token exist, or it expired
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token: #we have a refresh token
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'creds.json', SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open('token.json', 'w') as token:
            token.write(creds.to_json())

    return creds

# get a folder id
def getFolder(name, service):
    try:
        folderId = service.files().list(q=f"mimeType = 'application/vnd.google-apps.folder' and name = '{name}'",
                                        pageSize=10,
                                        fields="nextPageToken, files(id, name)").execute()
        folder = folderId.get('files', [])[0].get('id')
        return folder

    except HttpError as error:
        print(f'While searching for folder {name}, An error occurred: {error}')

# get the file ids/names of all files in a folder
def listFiles(folder, service, mimetype = None):
    if mimetype is not None:
        results = service.files().list(q=f"'{folder}' in parents and mimeType = '{mimetype}'", pageSize=10,
                                       fields="nextPageToken, files(id, name)").execute()
    else:
        results = service.files().list(q = f"'{folder}' in parents", pageSize=10,
                                       fields="nextPageToken, files(id, name, mimeType)").execute()
    return results.get('files', [])


# get a file id that can be exported
def downloadFile(file_id, service, asPdf = True):
    try:
        if asPdf:
            request = service.files().export_media(fileId=file_id, mimeType="application/pdf")
        else:
            request = service.files().get_media(fileId=file_id)

        file = io.BytesIO()
        downloader = MediaIoBaseDownload(file, request)
        done = False
        print()
        while not done:
            status, done = downloader.next_chunk()
            print(f'Downloading {file_id} {int(status.progress() * 100)}%', end = "\r")

        return file.getvalue()

    except HttpError as error:
        print(f'While exporting file with id: {file_id}, An error occurred: {error}')

# get a file id as a list of images
def getIMG(file_id, service):
    pdfData = downloadFile(file_id, service)
    return pdf2image.convert_from_bytes(pdfData)

# renew the buffer folder with files from remote
def updateSlides(folder, buffer):
    if not os.path.exists(buffer):
        os.mkdir(buffer)

    for i in os.listdir(buffer):
        os.remove(f"{buffer}/{i}")

    # authenticate
    creds = auth()
    service = build('drive', 'v3', credentials=creds)
    # fetch ids
    folder = getFolder(folder, service)
    files = listFiles(folder, service)
    # download files
    for i in files:
        if i["mimeType"] == "video/mp4":
            with open(f"{buffer}/{i['name']}", "wb") as file:
                file.write(downloadFile(i["id"], service, False))
        else:
            data = getIMG(i["id"], service)
            for j in range(len(data)):
                data[j].save(f"{buffer}/{i['name']}-{j}.png")

# display the buffer as a slideshow
def display(delay, buffer):
    os.system(f"vlc {buffer}/* --no-video-title-show --fullscreen --loop --image-duration={delay}")

def main():
    args = parser.parse_args()
    if not args.noUpdate:
        updateSlides(args.folder, os.path.abspath(args.buffer))
    if not args.noDisplay:
        display(args.delay, os.path.abspath(args.buffer))

main()