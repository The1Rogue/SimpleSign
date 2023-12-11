# SimpleSign
SimpleSign is a low maintenance, easy to set up and use system for digital signage, utilizing the to everyone familiar format of powerpoint / presentations.

### Setup

##### Credentials
since this is an open source repo and i don't want to have to care to much about credentials and security, you will have to get your own api key,
which can be done here: https://console.cloud.google.com/apis/

place the credentials in the same folder as `main.py`, and name the file `creds.json`

##### Drive setup
in a Google Drive account of your choosing, create a directory. any files in this directory will be used and displayed by SimpleSign, most notably, google presentations for slides and mp4 files for videos.
clone this repository onto the designated device which will display the signage.
run `python main.py [folder]` where folder is the name of the folder you created. the first time this is run, a browser will prompt you to log in to link your Google account.
after that the files will be downloaded, converted and subsequently displayed.
it is recommended that this program is set to run automatically after booting.

##### Requirements
to authenticate to google, a web-browser is required on the target system. this is not necessary if the display only is used, and files are manually placed into the buffer.

`vlc` is required for displaying the result.

for all systems the following python packages are needed:
`pdf2image, google-api-python-client, google-auth-oauthlib`

### Settings
`-d / --delay` sets the time every slide is shown for, in seconds, defaults to 10s.

`-b / --buffer` files fetched from the drive will be stored locally in the folder provided, defaults to buf/

`--no-display` when present, will only download and update the buffer, without displaying its contents. which means no graphical environment needs to be present.

`--no-update` when present, will not download any files, and only display what is present in the buffer. requires no authentication.

