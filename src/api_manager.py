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


import os
import re
from typing import Optional
from urllib.parse import urlparse

import requests
from chimerax.core.errors import NonChimeraXError
from requests import Response

from .utils import check_file_size

"""
All network call functionality for the Schol-AR API
"""

PROJECT_TYPES = {
    "Scientific Paper": "paper",
    "Poster or Other Presentation": "poster",
    "Book or Chapter": "book",
    "Other": "other"
}

PROJECT_TITLE_KEY = 'project_title'
PROJECT_TYPE_KEY = 'project_type'
PROJECT_DISC_URL_KEY = 'disc_url'
PROJECT_QRSTRING_KEY = 'QRString'
PUBLIC_QR_KEY = "QR_Image1"
ADMIN_QR_KEY = "AdminQRImage"
AUGMENTATION_TITLE_KEY = 'augmentation_title'
AUGMENTATION_TYPE_KEY = 'augmentation_type'
AUGMENTATION_INTERNAL_ID_KEY = 'internal_augid'
AUGMENTATION_AUG_FILE_KEY = 'augmented_file'
AUGMENTATION_TARGET_KEY = 'target_image'
AUGMENTATION_TRACKING_SCORE_KEY = 'targetimage_trackscore'

MAX_FILE_SIZE_MB = 30

# This should get set when the bundle is initialized
logger = None


def try_api_request(request_fn, *args, **kwargs) -> Optional[dict]:
    """
    Try to make an API request and return the response if successful. Print an error message if the request fails.

    :param request_fn: Function to make the API request. Must return a requests.Response object
    :param args: Positional arguments for the request function
    :param kwargs: Keyword arguments for the request function
    :return: JSON response from the API if the request is successful, None if the request fails
    """
    response: Response = None
    try:
        response = request_fn(*args, **kwargs)
        response.raise_for_status()  # Raises a HTTPError if the response status is 4xx, 5xx
        return response.json()
    except requests.exceptions.RequestException as e:
        if response is None:
            # The request did not make it to the server
            logger.error(f"An error occurred before the Schol-AR network request finished. \n Error: \n{e}")
            return None
        if 500 <= response.status_code < 600:
            raise NonChimeraXError(f"Schol-AR server error occurred making the API call: \n{response.url}"
                                   f"\n Error: \n{e}")
        else:
            logger.error(f"An error occurred while making the Schol-AR network call: \n{response.url}\n Error: \n{e}")
        return None


def validate_api_token(api_token: str) -> bool:
    """
    Make a standard project request to the api to validate the api token

    :param api_token: The API token to validate.
    :return: True if the api token is valid, False if it is not
    """
    url = 'https://www.Schol-AR.io/api/ListARP'
    headers = {'Authorization': f'Token {api_token}'}
    response = None
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        return True
    except requests.exceptions.RequestException as e:
        if response is None:
            logger.error(f"An error occurred before the Schol-AR network request finished. \n Error: \n{e}")
            return False
        elif 500 <= response.status_code < 600:
            raise NonChimeraXError(f"Schol-AR server error occurred making the API call: \n{response.url}"
                                   f"\n Error: \n{e}")
        elif response.status_code == 401:
            # This status code means the authorization was invalid
            return False
        else:
            logger.error(f"An error occurred while making the Schol-AR network call: \n{response.url}\n Error: \n{e}")
            return False


def list_arp_projects(api_token: str) -> Optional[dict]:
    """
    Make a call to the Schol-AR API to list all projects

    :param api_token: The API token for authorization.
    :return: JSON response from the API. None if failed response.
    """
    url = 'https://www.Schol-AR.io/api/ListARP'
    headers = {'Authorization': f'Token {api_token}'}
    return try_api_request(requests.get, url, headers=headers)


def create_project(api_token: str, project_title: str, project_type: str, disc_url: str) -> Optional[dict]:
    """
    Make a call to the Schol-AR API to create a new project

    :param api_token: The API token for authorization.
    :param project_title: The title of the project.
    :param project_type: The type of the project.
    :param disc_url: The URL for the project.
    :return: JSON response from the API. None if failed response.
    """
    url = 'https://www.Schol-AR.io/api/CreateARP'
    headers = {
        'Authorization': f'Token {api_token}',
        # For some reason Schol-ar requires specifying this header with json content type to avoid an error
        'Content-Type': 'application/json'
    }
    data = {
        PROJECT_TITLE_KEY: project_title,
        PROJECT_TYPE_KEY: project_type,
        PROJECT_DISC_URL_KEY: disc_url
    }
    return try_api_request(requests.post, url, headers=headers, json=data)


def get_qr_data(token: str, qr_string: str) -> Optional[dict]:
    """
    Make a call to the API to retrieve cloud URLs for QR code images.

    :param token: The API token for authorization.
    :param qr_string: The QR string to retrieve data for.
    :return: JSON response from the API. None if failed response.
    """
    url = f'https://www.Schol-AR.io/api/GetQR/{qr_string}'
    headers = {'Authorization': f'Token {token}'}
    return try_api_request(requests.get, url, headers=headers)


def list_augs(api_token: str, qr_string: str) -> Optional[dict]:
    """
    Make a call to the Schol-AR API to list all augmentations for a project.

    :param api_token: The API token for authorization.
    :param qr_string: The QR string to list augmentations for.
    :return: JSON response from the API. None if failed response.
    """
    url = f'https://www.Schol-AR.io/api/ListAug/{qr_string}'
    headers = {'Authorization': f'Token {api_token}'}
    return try_api_request(requests.get, url, headers=headers)


def create_augmentation(
        token: str, qr_string: str, augmentation_title: str, augmentation_type: str) -> Optional[dict]:
    """
    Make a call to the Schol-AR API to create a new augmentation.

    :param token: The API token for authorization.
    :param qr_string: The QR string for the project.
    :param augmentation_title: The title of the augmentation.
    :param augmentation_type: The type of the augmentation.
    :return: JSON response from the API. None if failed response.
    """
    url = f'https://www.Schol-AR.io/api/CreateAug/{qr_string}'
    headers = {'Authorization': f'Token {token}'}
    data = {
        AUGMENTATION_TITLE_KEY: augmentation_title,
        AUGMENTATION_TYPE_KEY: augmentation_type,
    }
    return try_api_request(requests.post, url, headers=headers, json=data)


def edit_augmentation(token: str, qrstring: str, aug_id: str, file_path: str,
                      target_update: bool) -> Optional[dict]:
    """
    Make a call to the Schol-AR API to edit an existing augmentation.

    :param token: The API token for authorization.
    :param qrstring: The QR string for the project.
    :param aug_id: The ID of the augmentation to edit.
    :param file_path: The path to the file to upload.
    :param target_update: Whether the file is a target image update.
    :return: JSON response from the API. None if failed response.
    """
    if not check_file_size(file_path):
        print(f"File size too large. Must be less than {MAX_FILE_SIZE_MB}MB")
        return None

    url = f'https://www.Schol-AR.io/api/EditAug/{qrstring}/{aug_id}'
    headers = {'Authorization': f'Token {token}'}
    files = {}
    if target_update:
        files[AUGMENTATION_TARGET_KEY] = open(file_path, 'rb')
    else:
        files[AUGMENTATION_AUG_FILE_KEY] = open(file_path, 'rb')
    return try_api_request(requests.patch, url, headers=headers, files=files)


def download_file_from_url(url: str, save_dir: str):
    """
    Download a file from a URL and save it to a directory. The file will be assigned a name matching the name in the URL.

    :param url: URL to download the file from.
    :param save_dir: Directory to save the downloaded file into.
    """
    # Make a GET request to the URL
    response = requests.get(url)
    # Check if the request was successful
    if response.status_code == 200:
        # Extract the filename from the URL
        filename = extract_filename_from_url(url)
        # Construct the full path where the file will be saved
        file_path = os.path.join(save_dir, filename)
        # Open a file in binary write mode
        with open(file_path, 'wb') as file:
            # Write the content of the response to the file
            file.write(response.content)
    else:
        print(f"Failed to download the file. Status code: {response.status_code}")


def extract_filename_from_url(url: str) -> str:
    """
    Extract the filename from a cloud URL.

    :param url: Google cloud storage API URL.
    :return: Filename extracted from the URL.
    """
    parsed_url = urlparse(url)
    path = parsed_url.path
    filename = os.path.basename(path)

    # Protection against malicious file names
    return sanitize_file_name(filename)


def sanitize_file_name(filename: str) -> str:
    """
    Sanitize a filename by removing or replacing special characters.

    :param filename: The filename to sanitize.
    :return: Sanitized filename.
    """
    # Remove or replace special characters
    sanitized_file_name = re.sub(r'[<>:"/\\|?*\x00-\x1F]', '_', filename)
    # Replace path traversal
    sanitized_file_name = re.sub(r'\.\.', '_', sanitized_file_name)
    # Replace absolute paths
    sanitized_file_name = re.sub(r'^[\\/]', '_', sanitized_file_name)
    return sanitized_file_name