import json
import sys
import subprocess
import glob
import logging


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
        except Exception as e:
            logging.error("Unrar failed")
            logging.error(e)
    else:
        logging.info("No RAR Files Found")
    
## Load Configuration
config = load_config()

## Check for RAR files and extract if unrar_all is set to true
if config["unrar_all"]:
    unrar_files(torrent_path)

## Main Loop to process torrents by type

# Check for Config based on type
type_index = check_filter_index(torrent_tags["type"])

# Confirm a matching config section was found
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

logging.info("Processing Completed")