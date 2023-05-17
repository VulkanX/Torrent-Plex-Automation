# Torrent handler script for QBittorrent
# This script will be called by QBittorrent when a torrent is completed
# The script will check for RAR files and extract them if found
# The script will then check the tags of the torrent to determine if it is a TV Show or Movie
# The script will then copy the files to the correct location on the server based on Title and Season tags from the torrent
# All actions from the script are logged to a log file configurable in the configuration section of the script
# Requirement
# - QBittorrent 4.6 or higher for Tagging RSS feeds
# - RAR CLI installed and added to Environment Variables Path

# Library Improts
import os
import sys
import glob
import subprocess
import shutil
import time

# Configuration
# General
debug_output = False # Set to True to enable debug output to the CLI when running manually

# Media Sever Root
Server_Root = "P:"
TV_Root = "TV Shows"
Movie_Root = "Movies"

# Log file location
log_file = "torrent_log.txt"

# Display Script Arguments
torrent_name = sys.argv[1] # Torrent Name
torrent_cat = sys.argv[2] # Torrent Category
torrent_path = sys.argv[3] # Torrent Path
torrent_tags = sys.argv[4] if len(sys.argv[4]) <= 3 else dict(item.split(":") for item in sys.argv[4].split(",")) # Torrent Tags
torrent_id = sys.argv[5] or "00000000" # Torrent ID
torrent_content_path = sys.argv[6] # Torrent Content Path

# RAR Status
extracted = False # Will become true if RAR files are found and extracted
rar_files = [] # List of RAR files found

## Custom Functions

# Custom Logging Function
def log(file_name, message_obj):
    # Write CLI Output if debugging is true else write to log file
    if debug_output: 
        print(message_obj)
    else:
        script_path = os.path.dirname(os.path.realpath(sys.argv[0]))
        with open(script_path + "\\" + file_name, "a") as file_obj:
            file_obj.write(message_obj + "\n")
            file_obj.close()

# Log Request properties
log(log_file, f"{torrent_id} -- Processing -- Torrent::{torrent_name} - Category::{torrent_cat} - Path::{torrent_path}")
log(log_file, f"{torrent_id} -- Tags::{torrent_tags}")
log(log_file, f"{torrent_id} -- Content Path::{torrent_content_path}")

# Check for RAR files and unrar
log(log_file,f'{torrent_id} -- Checking for RAR Files...')
rar_files = []
for file in glob.glob(torrent_path + "\*.rar"):
    rar_files.append(file)
if len(rar_files) > 0:
    log(log_file, f"{torrent_id} -- RAR Files Found :: {rar_files}")
else:
    log(log_file, f"{torrent_id} -- No RAR Files Found")


# 30 second delay incase the torrent is still active in the client
if len(rar_files) > 0: 
    time.sleep(15)

# Extract RAR files - Regardless of any tags extract the RAR files so you don't have to do it later
if len(rar_files) > 0:
    # Extract files using subprocess
    log(log_file, f"{torrent_id} -- Extracting RAR Files...")
    try:
        rcode = (subprocess.run(["unrar", "x","-y", file, torrent_path + "\\extracted\\"])).returncode
        log(log_file, f"{torrent_id} -- RAR Files Extracted :: Result: {rcode}")
        if rcode == 0:
            extracted = True
        else:
            log(log_file, f"{torrent_id} -- ERROR :: RAR Extraction Failed :: {rcode}")
    except Exception as e:
        log(log_file, f"{torrent_id} -- ERROR :: RAR Extraction Failed")
        log(log_file, f"{torrent_id} -- ERROR :: {e}")


# Check if Torrent is tagged as TV or Movie by the Type tag from QBittorrent
if "type" in torrent_tags:
    if torrent_tags["type"] == "tvshow" and "title" in torrent_tags and "season" in torrent_tags and "year" in torrent_tags:
        log(log_file, f"{torrent_id} -- TV Show Detected :: {torrent_tags['title']} ({torrent_tags['year']}) - Season {torrent_tags['season']}")
        # Check if Server folder exists for this season and show
        destinationFolder = f'{Server_Root}\\{TV_Root}\\{torrent_tags["title"]} ({torrent_tags["year"]})\\Season {torrent_tags["season"]}'
        if os.path.exists(destinationFolder):
            log(log_file, f"{torrent_id} -- Directory Exists :: {destinationFolder}")
        else:
            log(log_file, f"{torrent_id} -- Directory Does Not Exist - Creating Directory Structure :: {destinationFolder}")
            os.makedirs(destinationFolder)
            log(log_file, f"{torrent_id} -- Directory Created :: {destinationFolder}")
        
        # check if there were rar files and copy the files from extracted into the destination folder else copy all mkv files to the server
        if extracted:
            log(log_file, f"{torrent_id} -- Copying Files... (TV Show) -- Extracted: {extracted}")
            for file in glob.glob(torrent_path + "\extracted\*.mkv"):
                shutil.copy(file, destinationFolder)
                log(log_file, f"{torrent_id} -- File Copied :: {file} > {destinationFolder}")
        else:
            log(log_file, f"{torrent_id} -- Checking for Single Torrent File :: Torrent_Path == 0 :: {(torrent_path == 0)}")
            if len(torrent_path) == 0:
                log(log_file, f"{torrent_id} -- Path is 0, attempting to copy torrent it self")
                shutil.copy(torrent_content_path, destinationFolder)
            else:
                log(log_file, f"{torrent_id} -- Copying Files... (TV Show) -- Extracted: {extracted}")
                for file in glob.glob(torrent_path + "\*.mkv"):
                    shutil.copy(file, destinationFolder)
                    log(log_file, f"{torrent_id} -- File Copied :: {file} > {destinationFolder}")

    ## Torrent file is a movie
    elif torrent_tags["type"] == "movie" and "title" in torrent_tags and "year" in torrent_tags:
        log(log_file, f"{torrent_id} -- Movie Detected :: {torrent_tags['title']} ({torrent_tags['year']})")
        destinationFolder = f'{Server_Root}\\{Movie_Root}\\{torrent_tags["title"]} ({torrent_tags["year"]})'
        log(log_file, f"{torrent_id} -- Destination Folder Processed :: {destinationFolder}")
        # Check if movie folder exists, if not create it then copy the movie files
        if os.path.exists(destinationFolder):
            log(log_file, f"{torrent_id} -- Directory Exists :: {destinationFolder}")
        else:
            log(log_file, f"{torrent_id} -- Directory Does Not Exist - Creating Directory Structure :: {destinationFolder}")
            os.makedirs(destinationFolder)
            log(log_file, f"{torrent_id} -- Directory Created :: {destinationFolder}")

        # check if there were rar files and copy the files from extracted into the destination folder else copy all mkv files to the server
        if extracted:
            log(log_file, f"{torrent_id} -- Copying Files... (Movie) -- Extracted: {extracted}")
            for file in glob.glob(torrent_path + "\\extracted\\*.mkv"):
                shutil.copy(file, destinationFolder)
                log(log_file, f"{torrent_id} -- File Copied :: {file} > {destinationFolder}")
        else:
            log(log_file, f"{torrent_id} -- Checking for Single Torrent File :: Len={len(torrent_path)}")
            # Check for solo file download vs in a folder
            if len(torrent_path) == 0:
                log(log_file, f"{torrent_id} -- Path is 0, attempting to copy torrent it self")
                shutil.copy(torrent_name, destinationFolder)
                log(log_file, f"{torrent_id} -- File Copied :: {torrent_name} > {destinationFolder}")
            else:
                for file in glob.glob(torrent_path + "\\*.mkv"):
                    shutil.copy(file, destinationFolder)
                    log(log_file, f"{torrent_id} -- File Copied :: {file} > {destinationFolder}")
log(log_file, f"{torrent_id} -- Processing Complete")