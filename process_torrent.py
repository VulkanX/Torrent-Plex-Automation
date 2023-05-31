## Python script to process Torrent files downloaded with QBittorrent client 4.6 or higher (https://www.qbittorrent.org/)
## This script is intended to be used as a "Run external program" script in QBittorrent
## This script will process the torrent file and move the files to a destination folder based on the torrent tags
## This script will also extract RAR files if the config option is set to true
## This script moves all files of the configured file types to the destination folder

## Requirements
# Python 3.8 or higher
# QBittorrent 4.6 or higher
# Unrar installed and in the system path (https://www.rarlab.com/rar_add.htm)

## Configuration
# This script requires a config.json file in the same directory as the script
# A template file named config_template.json is included in the repo


## Script Imports
import json
import sys
import subprocess
import glob
import logging
import os
import shutil


## Process Script Arguments
torrent_name = sys.argv[1] # Torrent Name
torrent_path = sys.argv[2] # Torrent Path
torrent_tags = sys.argv[3] if len(sys.argv[3]) <= 3 else dict(item.split(":") for item in sys.argv[3].split(",")) # Torrent Tags
torrent_id = sys.argv[4] or "00000000" # Torrent ID
torrent_content_path = sys.argv[5] # Torrent Content Path


## Configure Logging
logger = logging.getLogger()
logger.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s -- %(levelname)s -- ' + torrent_id + ' -- %(message)s')

# Console Logging
stdout_handler = logging.StreamHandler(sys.stdout)
stdout_handler.setLevel(logging.DEBUG)
stdout_handler.setFormatter(formatter)
logger.addHandler(stdout_handler)

# File Logging
file_handler = logging.FileHandler("script_log.txt")
file_handler.setLevel(logging.INFO)
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)


## Global RAR variables
rar_extracted = False # Will become true if RAR files are found and extracted
rar_files = [] # List of RAR files found in torrent_path

logging.basicConfig(filename='script_log.txt', filemode='a', level=logging.DEBUG, format='%(asctime)s %(levelname)s %(name)s %(message)s')
## Custom Functions

def load_config():
    json_data = open(".\config.json").read()
    config = json.loads(json_data)
    return config

def check_filter_index(torrent_type):
    filters = config["filters"]
    for index, filter in enumerate(filters):
        if filter["type"] == torrent_type:
            return index
    return -1


def gen_destination_string(filter_index, tags):
    destination = config["filters"][filter_index]["destination"]
    for key, value in tags.items():
        destination = destination.replace("%%" + key + "%%", value)
    return destination

def unrar_files(folder_path):
    rar_extracted = False
    # Get list of RAR files in torrent_path
    logging.info("Checking for RAR files...")
    for file in glob.glob(folder_path + "\*.rar"):
        rar_files.append(file)

    if len(rar_files) > 0:
        logging.info("RAR Files Found :: " + str(rar_files))
        # Unrar all files in torrent_path
        logging.info("Unraring files...")
        try:
            for file in rar_files:
                logging.info("Trying to Unrar -- " + file)
                rcode = subprocess.run(["unrar", "x", "-y", file, folder_path + "\\extracted\\"]).returncode
                if rcode == 0:
                    logging.info("Unrar complete")
                    rar_extracted = True
                else:
                    logging.info("Unrar failed")
                    rar_extracted = False
        except Exception as e:
            logging.error("Unrar failed")
            logging.error(e)
    else:
        logging.info("No RAR Files Found")
    return rar_extracted
    
## Load Configuration
config = load_config()

## Check for RAR files and extract if unrar_all is set to true
if config["unrar_all"]:
    unrar_files(torrent_path)

## Main Loop to process torrents by type

# Check config for the type and confirm a matching config section was found
type_index = check_filter_index(torrent_tags["type"])
if type_index == -1:
    logging.critical("No matching config section found for torrent type: " + torrent_tags["type"])
    exit()
else:
    logging.info("Found config section for torrent type: " + torrent_tags["type"])


# Confirm all required tags are present or exit
for tag in config["filters"][type_index]["required_tags"]:
    if tag not in torrent_tags:
        logging.critical("Missing required tag: " + tag)
        exit()

# Unrar files if rar files present
extracted_folder = True # Change if rar files found and extracted
# if config["filters"][type_index]["unrar"]:
#     extracted_folder = unrar_files(torrent_path)

# Generate the destination folder path
destination = gen_destination_string(type_index, torrent_tags)
logging.info("Destination Folder: " + destination)

# Check if destination folder exists, if not create it
logging.info("checking if destination folder exists")
if not os.path.exists(destination):
    logging.info("destination folder does not exist, creating it")
    os.makedirs(destination)
else:
    logging.info("destination folder exists")

# Check if rar was extracted and move configured file types from config to the destination
file_types = config["filters"][type_index]["file_types"]
logging.info("Checking if rar was extracted")
if extracted_folder:
    logging.info("RAR was extracted, moving file types [" + str(file_types) + "] to destination]")
    for file_type in file_types:
        for file in glob.glob(torrent_path + "\\extracted\*." + file_type):
            logging.info("Moving file: " + file)
            shutil.copy(file, destination)
    logging.info("Moving files complete")
else:
    # No Extraction happened so we check for a single torrent file download or a folder download
    logging.info("RAR was not extracted, checking for single file or folder download")
    if len(torrent_path) == 0:
        logging.info("Single file download")
        logging.info("Moving file [" + torrent_content_path + "] to destination")
        shutil.copy(torrent_content_path, destination)
    else:
        logging.info("Folder download")
        logging.info("Moving file types [" + str(file_types) + "] to destination")
        for file_type in file_types:
            for file in glob.glob(torrent_path + "\*." + file_type):
                logging.info("Moving file: " + file)
                shutil.copy(file, destination)
        logging.info("Moving files complete")
logging.info("Processing Completed")