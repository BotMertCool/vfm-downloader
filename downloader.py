from colorama import init, Fore
import requests
import subprocess
import time
import os
import re

init(convert=True)

print(Fore.GREEN + 'Paste in your Auth Token.')
print(Fore.GREEN + 'To get it run the command in, "cmd.txt" in the console of your "https://vault.fm/" page.')
print()

# Ask for users auth token
authToken = input("Auth Token: ")

print()
print(Fore.GREEN + 'Handle of the user you want songs from (Example: "jamesblake").')
# Ask for users auth token
handle = input("Artist Handle: ")

url = 'https://vault.fm/graphql'

def main():
    data = '{"query": "query ArtistByHandle($input: QueryArtistByLinkInput!) { artistByLink(input: $input) { mainVaultId } }", "variables": {"input":{"link":"' + handle + '"}}}'

    headers = {
        'Content-Type': 'application/json',
        'Auth-Token': authToken,
    }

    response = requests.post(url, headers=headers, data=data)


    response_data = response.json()
    vaultId = response_data['data']['artistByLink']['mainVaultId']

    getSongsFromIds(vaultId)

def getSongsFromIds(vaultId):
    data = '{"query":"query VaultTrackIds($vaultId:UUID!){vaultFromId(vaultId:$vaultId){id trackIds}}","variables":{"vaultId":"' + vaultId + '"}}'

    headers = {
        'Content-Type': 'application/json',
        'Auth-Token': authToken,
    }

    response = requests.post(url, headers=headers, data=data)
    response_data = response.json()

    # Access the track IDs
    track_ids = response_data['data']['vaultFromId']['trackIds']
    # Loop through the track IDs
    for track_id in track_ids:
        getSong(track_id)
        time.sleep(1)

def getSong(songId):
    data = '{"query":"query TrackContentById($vaultContentId:UUID!){vaultContentById(vaultContentId:$vaultContentId){__typename id ...on VaultTrack{createdAt title caption vault{id artist:artistProfile{id name linkValue profileImage{id url}}}}}getSignedTrackContent(trackContentId:$vaultContentId){__typename ...on QueryGetSignedTrackContentSuccess{data}}}","variables":{"vaultContentId":"' + songId + '"}}'

    headers = {
        'Content-Type': 'application/json',
        'Auth-Token': authToken,
    }

    response = requests.post(url, headers=headers, data=data)

    response_data = response.json()
    set_cookie_value = response.headers.get('Set-Cookie')
    audio_file_url = response_data['data']['getSignedTrackContent']['data']
    filename = response_data['data']['vaultContentById']['title']
    
    print(f"{Fore.YELLOW}[{handle}] Downloading {filename}...")
    
    if not os.path.exists(handle):
        os.makedirs(handle)

    new_cookie = set_cookie_value.split(';')[0]

    # Define the FFmpeg command
    if not os.path.exists(f'{handle}/{sanitize_filename(filename)}.m4a'):
        ffmpeg_cmd = [
            'ffmpeg',                          # Command
            "-headers", f"Cookie: {new_cookie}\r\n",
            '-protocol_whitelist',             # Protocol whitelist option
            'file,http,https,tcp,tls',         # Whitelisted protocols
            '-i',                              # Input file option
            audio_file_url, # Input file URL
            '-c', 'copy',                      # Codec option
            f'{handle}/{sanitize_filename(filename)}.m4a'                       # Output file
        ]

        try:
            subprocess.run(ffmpeg_cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            print(f"{Fore.YELLOW}[{handle}] {filename} downloaded successfully.")
        except subprocess.CalledProcessError as e:
            print("Error running FFmpeg command:", e)
    else:
        print(f"{Fore.YELLOW}[{handle}] {filename} already downloaded.")

def sanitize_filename(filename):
    # Define a regular expression pattern to match characters not allowed in Windows file names
    illegal_chars = r'[<>:"/\\|?*]'

    # Remove illegal characters from the filename using re.sub()
    sanitized_filename = re.sub(illegal_chars, '', filename)

    return sanitized_filename

main()