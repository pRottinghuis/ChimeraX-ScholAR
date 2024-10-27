# === UCSF ChimeraX Copyright ===
# Copyright 2024 Regents of the University of California. All rights reserved.
# The ChimeraX application is provided pursuant to the ChimeraX license
# agreement, which covers academic and commercial uses. For more details, see
# <https://www.rbvi.ucsf.edu/chimerax/docs/licensing.html>
#
# You can also
# redistribute and/or modify it under the terms of the GNU Lesser General
# Public License version 2.1 as published by the Free Software Foundation.
# For more details, see
# <https://www.gnu.org/licenses/old-licenses/lgpl-2.1.html>
#
# THIS SOFTWARE IS PROVIDED "AS IS" WITHOUT WARRANTY OF ANY KIND, EITHER
# EXPRESSED OR IMPLIED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES
# OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE. ADDITIONAL LIABILITY
# LIMITATIONS ARE DESCRIBED IN THE GNU LESSER GENERAL PUBLIC LICENSE
# VERSION 2.1
#
# This notice must be embedded in or attached to all copies, including partial
# copies, of the software or any revisions or derivations thereof.
# === UCSF ChimeraX Copyright ===


import json
import os
import shutil
from typing import Optional

from chimerax import app_dirs_unversioned
from chimerax.core.commands import run

from . import api_manager
from .utils import check_file_size, get_first_file

"""
This module provides all file management functionality for the Schol-AR CLI, including saving user data, projects, and augmentations.

It manages the following file structure, which is a slight adaptation of the Schol-AR API structure:

Schol-AR: Main directory
    - users_info.json: JSON file that holds all user data
    - user: Directory for each user
        - projects_info.json: JSON file that holds all project data for a user
        - project: Directory for each project
            - augmentations_info.json: JSON file that holds all augmentation data for a project
            - augmentation: Directory for each augmentation
                - target_image: Directory for target images
                - augmented_file: Directory for augmented files
                - cxs: Directory for cxs files
                - aug_info.json: JSON file that holds augmentation data
            - qr: Directory for QR codes
                - pub: Directory for public QR codes
                - admin: Directory for admin QR codes

Attributes:
    BASE_DIR (str): Base directory for Schol-AR data.
    USER_INFO_FILE (str): Filename for storing user information.
    USERS_INFO_PATH (str): Full path to the user information file.
    PROJECT_INFO_FILE (str): Filename for storing project information.
    QR_DIR (str): Directory name for storing QR code images.
    AUGMENTATIONS_INFO_FILE (str): Filename for storing augmentation information.
    AUG_TARGET_IMAGE_DIR (str): Directory name for storing target images.
    AUG_MODEL_DIR (str): Directory name for storing augmented files.
    AUG_SESSION_DIR (str): Directory name for storing session files.
    active_user_key (tuple): Cache for the active user and their API token.
"""

BASE_DIR = os.path.join(app_dirs_unversioned.user_data_dir, "Schol-AR")

USER_INFO_FILE = "users_info.json"
USERS_INFO_PATH = os.path.join(BASE_DIR, USER_INFO_FILE)

# Directory used for file size checks
TEMP_DIR = os.path.join(BASE_DIR, "temp")

PROJECT_INFO_FILE = "projects_info.json"
QR_DIR = "qr"
AUGMENTATIONS_INFO_FILE = "augmentations_info.json"

AUG_TARGET_IMAGE_DIR = "target_image"
AUG_MODEL_DIR = "augmented_file"
AUG_SESSION_DIR = "cxs"

# used like a cache to avoid repeated file reads
active_user_key = (None, None)


def username_exists(username: str) -> bool:
    """
    Check if a username exists in the user_info.json file.

    :param username: The username to check.
    :return: True if the username exists, False otherwise.
    """
    users_info = get_users_info()
    if users_info is None:
        return False
    return username in users_info.keys()


def project_exists(username: str, project_title: str) -> bool:
    """
    Check if a project exists in the projects_info.json file.

    :param username: The username to check.
    :param project_title: The project title to check.
    :return: True if the project exists, False otherwise.
    """
    projects_info = get_projects_info(username)
    if projects_info is None:
        return False
    return any(project.get(api_manager.PROJECT_TITLE_KEY) == project_title for project in projects_info)


def aug_exists(username: str, project_title: str, augmentation_title: str) -> bool:
    """
    Check if an augmentation exists in the augmentations_info.json file.

    :param username: The username to check.
    :param project_title: The project title to check.
    :param augmentation_title: The augmentation title to check.
    :return: True if the augmentation exists, False otherwise.
    """
    augmentations_info = get_augs_info(username, project_title)
    if augmentations_info is None:
        return False
    return any(aug.get(api_manager.AUGMENTATION_TITLE_KEY) == augmentation_title for aug in augmentations_info)


def list_usernames() -> list:
    """
    Get an array of all existing usernames.

    :return: An array of all existing usernames.
    """
    users_info = get_users_info()
    if users_info is None:
        return []
    return list(users_info.keys())


def remove_user(username: str) -> bool:
    """
    Remove a username-api-token pairing from the user_info.json file and delete all user data.
    :param username: Username to remove from the file
    :return: True if the username was removed, False if the username doesn't exist
    """

    # This will inherently also make sure that the user_info file exists
    if not username_exists(username):
        return False

    # Delete the entire user directory if the user's API token is invalid
    user_dir = os.path.join(BASE_DIR, username)
    shutil.rmtree(user_dir)

    users_info = get_users_info()
    users_info.pop(username)

    with open(USERS_INFO_PATH, 'w') as file:
        json.dump(users_info, file, indent=4)
    return True


def init_scholar_dirs():
    """
    Initialize the user structure with a base directory and user_info.json file. Initialize the Schol-AR main
    directory if this is the first time a Schol-AR command is used.
    """
    # Define the path for the user_info.json file
    user_info_path = USERS_INFO_PATH

    # Check if the user_info.json file already exists
    if not os.path.exists(user_info_path):
        # If it does not exist, create the initial structure of the JSON
        initial_data = {}

        # Ensure the base directory exists
        os.makedirs(BASE_DIR, exist_ok=True)

        # Write the initial data to the user_info.json file
        with open(user_info_path, 'w') as file:
            json.dump(initial_data, file, indent=4)


def get_project_dir(username: str, project_title: str) -> str:
    """
    Get or create the directory path for a specific project.

    :param username: The username to check.
    :param project_title: The project title to check.
    :return: The directory path for the project.
    """
    project_dir = get_project_dir_name(username, project_title)
    os.makedirs(project_dir, exist_ok=True)
    return project_dir


def get_project_dir_name(username: str, project_title: str) -> str:
    """
    Get the directory path for a specific project.

    :param username: The username to check.
    :param project_title: The project title to check.
    :return: The directory path for the project.
    """
    qr_string = get_project_qrstring(username, project_title)
    project_dir = os.path.join(BASE_DIR, username, qr_string)
    return project_dir


def get_aug_dir(username: str, project_title: str, augmentation_title: str) -> str:
    """
    Get the directory path for a specific augmentation.

    :param username: The username to check.
    :param project_title: The project title to check.
    :param augmentation_title: The augmentation title to check.
    :return: The directory path for the augmentation.
    """
    aug_dir = get_aug_dir_name(username, project_title, augmentation_title)
    os.makedirs(aug_dir, exist_ok=True)
    return aug_dir


def get_aug_dir_name(username: str, project_title: str, augmentation_title: str) -> str:
    """
    Get the directory path for a specific augmentation.

    :param username: The username to check.
    :param project_title: The project title to check.
    :param augmentation_title: The augmentation title to check.
    :return: The directory path for the augmentation.
    """
    project_dir = get_project_dir(username, project_title)
    aug_id = get_augmentation_id(username, project_title, augmentation_title)
    aug_dir = os.path.join(project_dir, aug_id)
    return aug_dir


def update_users_info(username: str, api_token: str):
    """
    Save/Update a user API token key-value pair into a save file.

    :param username: The username to add to the user save file. Must be validated first.
    :param api_token: The API token to add to the user save file. Must be validated first.
    """
    # Get the current user info
    users_save_file = get_users_info()

    users_save_file[username] = api_token

    # Write the updated user info back to the save file
    with open(USERS_INFO_PATH, 'w') as file:
        json.dump(users_save_file, file, indent=4)

    # make sure directory for the user trying to log in exists
    user_dir = os.path.join(BASE_DIR, username)
    os.makedirs(user_dir, exist_ok=True)

    active_user_key = (username, api_token)


def get_user_token(username: str) -> Optional[str]:
    """
    Get the API token from a username out of the user save file otherwise return None.

    :param username: The username to get the API token for.
    :return: The API token if found, None otherwise.
    """
    # avoid going through full file check if we keep asking the same user for the key
    active_user, active_key = active_user_key
    if active_user == username:
        return active_key

    # the username does not match the "cached" name
    users_info = get_users_info()
    if users_info is None:
        print("Failed to get user info save file to fetch user token")
        return None
    api_token = users_info.get(username)
    return api_token


def get_users_info() -> Optional[dict]:
    """
    Get the users save file as a JSON dictionary.

    :return: The users save file as a JSON dictionary.
    """
    # Check if the user_info.json file exists at the specified path
    if not os.path.exists(USERS_INFO_PATH):
        # If the file does not exist, return None or an empty dictionary
        return None
    else:
        # If the file exists, open it and load the JSON data
        with open(USERS_INFO_PATH, 'r') as file:
            users_info = json.load(file)
        return users_info


def get_projects_info_path(username: str) -> str:
    """
    Get the path to the projects save file for a user.

    :param username: The username to get the projects save file path for.
    :return: The path to the projects save file.
    """
    return os.path.join(BASE_DIR, username, PROJECT_INFO_FILE)


def get_projects_info(username: str) -> Optional[dict]:
    """
    Get the projects save file as a JSON dictionary.

    :param username: The username to get the projects save file for.
    :return: The projects save file as a JSON dictionary.
    """
    projects_info_path = get_projects_info_path(username)

    # Check if the projects_info.json file exists
    if not os.path.exists(projects_info_path):
        return None

    # Open the projects_info.json file and load its contents
    with open(projects_info_path, 'r') as file:
        projects_info = json.load(file)

    return projects_info


def update_user_projects(username: str):
    """
    API call and save response list of projects for a user into a save file.

    :param username: The username to update the projects for.
    """
    if not username_exists(username):
        return
    token = get_user_token(username)
    list_arp_response = api_manager.list_arp_projects(token)
    if list_arp_response is None:
        print("Failed to retrieve user projects")
        return

    save_file_path = get_projects_info_path(username)
    with open(save_file_path, 'w') as file:
        json.dump(list_arp_response, file, indent=4)


def get_project(username: str, project_title: str) -> Optional[dict]:
    """
    Retrieve a project's JSON data from the user's projects save file.

    :param username: The username to get the project for.
    :param project_title: The project title to get the project data for.
    :return: The project JSON data if found, None otherwise.
    """
    if not project_exists(username, project_title):
        return None
    projects_info = get_projects_info(username)

    # Check if the project title exists in the list of projects and return the project data if found
    for project in projects_info:
        if project.get(api_manager.PROJECT_TITLE_KEY) == project_title:
            return project

    # If no matching project found, return None
    return None


def list_projects(username: str) -> list:
    """
    Get an array of all existing project titles for a user.

    :param username: The username to list the projects for.
    :return: An array of all existing project titles.
    """
    projects_info = get_projects_info(username)
    if projects_info is None:
        return []

    return [project.get(api_manager.PROJECT_TITLE_KEY) for project in projects_info]


def get_project_qrstring(username: str, project_title: str) -> Optional[str]:
    """
    Get the QRString for a project or None if the project does not exist in the user's project save file.

    :param username: The username to get the QRString for.
    :param project_title: The project title to get the QRString for.
    :return: The QRString if found, None otherwise.
    """
    if not project_exists(username, project_title):
        return None
    project = get_project(username, project_title)
    return project.get(api_manager.PROJECT_QRSTRING_KEY)


def pub_qr_dir(username: str, project_title: str) -> str:
    """
    Create the directory that the QR codes need to go into for a project.

    :param username: The username to create the QR directory for.
    :param project_title: The project title to create the QR directory for.
    :return: The path to the public QR code directory.
    """
    project_dir = get_project_dir(username, project_title)
    qr_dir = os.path.join(project_dir, QR_DIR, "pub")
    os.makedirs(qr_dir, exist_ok=True)
    return qr_dir


def admin_qr_dir(username: str, project_title: str) -> str:
    """
    Create the directory that the QR codes need to go into for a project.

    :param username: The username to create the QR directory for.
    :param project_title: The project title to create the QR directory for.
    :return: The path to the admin QR code directory.
    """
    project_dir = get_project_dir(username, project_title)
    qr_dir = os.path.join(project_dir, QR_DIR, "admin")
    os.makedirs(qr_dir, exist_ok=True)
    return qr_dir


def get_qr_file(username: str, project_title: str, admin: bool) -> Optional[str]:
    """
    Get the full path to the QR code file for a project.

    :param username: The username to get the QR file for.
    :param project_title: The project title to get the QR file for.
    :param admin: Boolean indicating if the QR file is for admin. False for public QR.
    :return: The path to the QR code file or None if not found.
    """
    qr_dir = admin_qr_dir(username, project_title) if admin else pub_qr_dir(username, project_title)
    file_name = get_first_file(qr_dir)
    if file_name is None:
        return None
    return os.path.join(qr_dir, file_name)


def update_augs_info(username: str, project_title: str):
    """
    Make an API call that lists the augmentations for a project and update the project's save file.

    :param username: The username to update the augmentations for.
    :param project_title: The project title to update the augmentations for.
    """
    if not project_exists(username, project_title):
        return

    token = get_user_token(username)
    qrstring = get_project_qrstring(username, project_title)

    # update the project save file
    list_augs_response = api_manager.list_augs(token, qrstring)
    if list_augs_response is None:
        print(
            f"Failed to retrieve project augmentations to update for user: {username} project: {project_title}"
        )
        return

    # Construct the path to the project directory and ensure it exists
    project_dir_path = get_project_dir(username, project_title)
    os.makedirs(project_dir_path, exist_ok=True)

    # Construct the path to the aug_info.json file within the project directory
    augs_info_path = os.path.join(project_dir_path, AUGMENTATIONS_INFO_FILE)
    # Write the aug_info_data to the aug_info.json file
    with open(augs_info_path, 'w') as file:
        json.dump(list_augs_response, file, indent=4)


def init_aug_dirs(username: str, project_title: str, augmentation_title: str, create_aug_response: dict):
    """
    Create the directory structure for the augmentation.

    :param username: The username to create the augmentation directories for.
    :param project_title: The project title to create the augmentation directories for.
    :param augmentation_title: The augmentation title to create the directories for.
    :param create_aug_response: The response from the API call to create the augmentation.
    """
    aug_target_dir(username, project_title, augmentation_title)
    aug_model_dir(username, project_title, augmentation_title)
    aug_session_dir(username, project_title, augmentation_title)


def get_augmentation(username: str, project_title: str, augmentation_title: str) -> Optional[dict]:
    """
    Get the JSON data for an augmentation or None if the augmentation does not exist in the project's augmentations
    save file.

    :param username: The username to get the augmentation for.
    :param project_title: The project title to get the augmentation for.
    :param augmentation_title: The augmentation title to get the data for.
    :return: The JSON data for the augmentation if found, None otherwise.
    """
    augmentations_info = get_augs_info(username, project_title)

    # Check if the aug title exists in the list of augs and return the aug data if found
    for augmentation in augmentations_info:
        if augmentation.get(api_manager.AUGMENTATION_TITLE_KEY) == augmentation_title:
            return augmentation

    # If no matching augmentation, return None
    return None


def list_existing_aug_titles(username: str, project_title: str) -> list:
    """
    Get an array of all existing augmentation titles for a project.

    :param username: The username to list the augmentations for.
    :param project_title: The project title to list the augmentations for.
    :return: An array of all existing augmentation titles.
    """
    augs_info = get_augs_info(username, project_title)
    if augs_info is None:
        return []

    return [aug.get(api_manager.AUGMENTATION_TITLE_KEY) for aug in augs_info]


def get_augs_info(username, project_title) -> Optional[dict]:
    """
    Get the augmentations save file as a JSON dictionary.

    :param username: The username to get the augmentations for.
    :param project_title: The project title to get the augmentations for.
    :return: The augmentations save file as a JSON dictionary.
    """
    project_augmentations_dir = get_project_dir(username, project_title)
    augs_info_path = os.path.join(project_augmentations_dir, AUGMENTATIONS_INFO_FILE)

    # Check if the augs info save file exists
    if not os.path.exists(augs_info_path):
        return None

    # Open the augs info save file and load its contents
    with open(augs_info_path, 'r') as file:
        augmentations_info = json.load(file)

    return augmentations_info


def aug_target_dir(username: str, project_title: str, augmentation_title: str) -> str:
    """
    Get (create if not existing) a full path for a standard aug target directory.

    :param username: The username to get the target directory for.
    :param project_title: The project title to get the target directory for.
    :param augmentation_title: The augmentation title to get the target directory for.
    :return: The full path for the target directory.
    """
    base_aug_dir = get_aug_dir(username, project_title, augmentation_title)
    target_dir = os.path.join(base_aug_dir, AUG_TARGET_IMAGE_DIR)
    # trying to make the directory if it does not exist allows this to be used like a getter for the directory path
    # at times when it may not exist yet. Useful in the case of creating a new augmentation where files have to be
    # downloaded to create an augmentation.
    os.makedirs(target_dir, exist_ok=True)
    return target_dir


def aug_model_dir(username: str, project_title: str, augmentation_title: str) -> str:
    """
    Get (create if not existing) a full path for a standard aug model directory.

    :param username: The username to get the model directory for.
    :param project_title: The project title to get the model directory for.
    :param augmentation_title: The augmentation title to get the model directory for.
    :return: The full path to the augmentation model directory.
    """
    base_aug_dir = get_aug_dir(username, project_title, augmentation_title)
    target_dir = os.path.join(base_aug_dir, AUG_MODEL_DIR)
    os.makedirs(target_dir, exist_ok=True)
    return target_dir


def aug_session_dir(username: str, project_title: str, augmentation_title: str) -> str:
    """
    Get (create if not existing) a full path for a standard aug session directory.

    :param username: The username to get the session directory for.
    :param project_title: The project title to get the session directory for.
    :param augmentation_title: The augmentation title to get the session directory for.
    :return: The full path to the augmentation session directory.
    """
    base_aug_dir = get_aug_dir(username, project_title, augmentation_title)
    target_dir = os.path.join(base_aug_dir, AUG_SESSION_DIR)
    os.makedirs(target_dir, exist_ok=True)
    return target_dir


def aug_target_file(username: str, project_title: str, augmentation_title: str) -> str:
    """
    Get (create if not existing) a full path for a standard aug target file.

    :param username: The username to get the target file for.
    :param project_title: The project title to get the target file for.
    :param augmentation_title: The augmentation title to get the target file for.
    :return: The full path to the augmentation target file.
    """
    target_name = augmentation_title + "-target.png"
    return os.path.join(aug_target_dir(username, project_title, augmentation_title), target_name)


def aug_model_file(username: str, project_title: str, augmentation_title: str) -> str:
    """
    Get (create if not existing) a full path for a standard aug model file.

    :param username: The username to get the model file for.
    :param project_title: The project title to get the model file for.
    :param augmentation_title: The augmentation title to get the model file for.
    :return: The full path to the augmentation model file.
    """
    model_name = augmentation_title + "-model.glb"
    return os.path.join(aug_model_dir(username, project_title, augmentation_title), model_name)


def aug_session_file(username: str, project_title: str, augmentation_title: str) -> str:
    """
    Get (create if not existing) a full path for a standard aug session file.

    :param username: The username to get the session file for.
    :param project_title: The project title to get the session file for.
    :param augmentation_title: The augmentation title to get the session file for.
    :return: The full path to the augmentation session file.
    """
    session_name = augmentation_title + "-session.cxs"
    return os.path.join(aug_session_dir(username, project_title, augmentation_title), session_name)


def has_session_file(username: str, project_title: str, augmentation_title: str) -> bool:
    """
    Check if a session file exists for an augmentation.

    :param username: The username to check.
    :param project_title: The project title to check.
    :param augmentation_title: The augmentation title to check.
    :return: True if the session file exists, False otherwise.
    """
    # Check if there is a session file in the augmentation session directory
    session_dir = aug_session_dir(username, project_title, augmentation_title)
    return get_first_file(session_dir).endswith('.cxs') if get_first_file(session_dir) else False


def get_augmentation_target_url(username: str, project_title: str, augmentation_title: str) -> Optional[str]:
    """
    Get the URL for the target image of an augmentation.

    :param username: The username to get the target URL for.
    :param project_title: The project title to get the target URL for.
    :param augmentation_title: The augmentation title to get the target URL for.
    :return: The URL for the target image if found, None otherwise.
    """
    aug = get_augmentation(username, project_title, augmentation_title)
    return aug.get(api_manager.AUGMENTATION_TARGET_KEY)


def get_augmentation_model_url(username: str, project_title: str, augmentation_title: str) -> Optional[str]:
    """
    Get the URL for the model file of an augmentation.

    :param username: The username to get the model URL for.
    :param project_title: The project title to get the model URL for.
    :param augmentation_title: The augmentation title to get the model URL for.
    :return: The URL for the model file if found, None otherwise.
    """
    if not aug_exists(username, project_title, augmentation_title):
        return None
    aug = get_augmentation(username, project_title, augmentation_title)
    return aug.get(api_manager.AUGMENTATION_AUG_FILE_KEY)


def get_augmentation_id(username, project_title, augmentation_title):
    """
    Get the internal ID for an augmentation.

    :param username: The username to get the augmentation ID for.
    :param project_title: The project title to get the augmentation ID for.
    :param augmentation_title: The augmentation title to get the augmentation ID for.
    :return: The internal ID for the augmentation if found, None otherwise.
    """
    aug = get_augmentation(username, project_title, augmentation_title)
    return aug.get(api_manager.AUGMENTATION_INTERNAL_ID_KEY)


def get_aug_tracking_score(username, project_title, augmentation_title):
    """
    Get the tracking score for an augmentation.

    :param username: The username to get the tracking score for.
    :param project_title: The project title to get the tracking score for.
    :param augmentation_title: The augmentation title to get the tracking score for.
    :return: The tracking score if found, None otherwise.
    """
    aug = get_augmentation(username, project_title, augmentation_title)
    return aug.get(api_manager.AUGMENTATION_TRACKING_SCORE_KEY)


def get_augmentation_target_image_path(username: str, project_title: str,
                                       augmentation_title: str) -> Optional[str]:
    """
    Get the local file path for the target image of an augmentation.

    :param username: The username to get the target image path for.
    :param project_title: The project title to get the target image path for.
    :param augmentation_title: The augmentation title to get the target image path for.
    :return: The local file path for the target image if found, None otherwise.
    """
    target_dir = aug_target_dir(username, project_title, augmentation_title)
    first_file = get_first_file(target_dir)
    if first_file:
        return os.path.join(target_dir, first_file)
    return None


def get_auggmentation_model_file_path(username: str, project_title: str, augmentation_title: str) -> Optional[str]:
    """
    Get the local file path for the model file of an augmentation.

    :param username: The username to get the model file path for.
    :param project_title: The project title to get the model file path for.
    :param augmentation_title: The augmentation title to get the model file path for.
    :return: The local file path for the model file if found, None otherwise.
    """
    model_dir = aug_model_dir(username, project_title, augmentation_title)
    first_file = get_first_file(model_dir)
    if first_file:
        return os.path.join(model_dir, first_file)
    return None


def clean_local(username: str):
    """
    Clean all local files that are associated with projects or augmentations that no longer exist on Schol-AR.

    :param username: The username to clean the local files for.
    """
    if not username_exists(username):
        return

    if not api_manager.validate_api_token(get_user_token(username)):
        api_manager.logger.warning(f"Found user: {username} with an invalid API token. Consider deleting the user.")
        return

    # Make sure that the user's projects are up-to-date
    update_user_projects(username)

    projects_info = get_projects_info(username)
    if projects_info is None:
        return

    # collect an array of all expected project dir names from the save file.
    expected_project_dirs = [
        get_project_dir_name(username, project[api_manager.PROJECT_TITLE_KEY]) for project in projects_info
    ]
    user_base_dir = os.path.join(BASE_DIR, username)

    # iterate through all the dirs in the user's base dir and remove any that are not an expected name
    for item in os.listdir(user_base_dir):
        item_path = os.path.join(user_base_dir, item)
        if os.path.isdir(item_path) and item_path not in expected_project_dirs:
            shutil.rmtree(item_path)

    # For each project, update the augmentations and clean up augmentation directories
    for project in projects_info:
        project_title = project[api_manager.PROJECT_TITLE_KEY]
        update_augs_info(username, project_title)

        augmentations_info = get_augs_info(username, project_title)
        if augmentations_info is None:
            continue

        # Collect an array of all expected augmentation dir names from the save file
        expected_aug_dirs = [
            get_aug_dir_name(username, project_title, aug[api_manager.AUGMENTATION_TITLE_KEY]) for aug in
            augmentations_info
        ]
        project_dir = get_project_dir(username, project_title)

        # Iterate through all the aug dirs in the project dir and remove any that are not an expected aug name
        for item in os.listdir(project_dir):
            item_path = os.path.join(project_dir, item)
            if os.path.isdir(item_path) and item_path not in expected_aug_dirs:
                shutil.rmtree(item_path)


def save_and_size_check(session, file_extension: str, verbose: bool = False):
    """
    Save a file to a temporary directory, check if it is within the allowed Schol-AR size, and then delete it.

    :param session: The current ChimeraX session.
    :param file_extension: The desired file extension for the saved file (e.g., ".png").
    :param verbose: If True, the command will log additional information. Default is False.
    :return: True if the file size is within the allowed limit, False otherwise.
    """
    # Create a temporary directory to save the file
    os.makedirs(TEMP_DIR, exist_ok=True)
    # Save the file to the temporary directory
    file_name = f"scholar-file-check{file_extension}"
    file_path = os.path.join(TEMP_DIR, file_name)
    run(session, f"save \"{file_path}\"", log=verbose)
    # Check if the file size is within the allowed limit
    is_within_size_limit = check_file_size(file_path)
    # Delete the entire temporary directory
    shutil.rmtree(TEMP_DIR)
    return is_within_size_limit
