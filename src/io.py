import json
import os
import re
import shutil
from urllib.parse import urlparse

import requests
from chimerax import app_dirs_unversioned
from requests import Response


class APIManager:
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

    @staticmethod
    def try_api_request(request_fn, display_errors: bool, *args, **kwargs) -> dict | None:
        """
        Try to make an API request and return the response if successful. Print an error message if the request fails.
        :param display_errors: Should there be errors printed on a failed request
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
            if display_errors:
                if response is not None:
                    # The request was made but the server returned an error
                    print(f"An error occurred while making the API call: \n{response.url}\n Error: \n{e}")
                else:
                    # The request was not made to the server
                    print(f"An error occurred while making the API call: \n{e}")
            return None

    @staticmethod
    def validate_api_token(api_token: str) -> bool:
        """
        Make a standard project request to the api to validate the api token
        :return: True if the api token is valid, False if it is not
        """
        url = 'https://www.Schol-AR.io/api/ListARP'
        headers = {'Authorization': f'Token {api_token}'}
        # We don't need to display errors. What goes wrong doesn't concern the user here.
        response = APIManager.try_api_request(requests.get, False, url, headers=headers)
        if response is None:
            return False
        else:
            return True

    @staticmethod
    def list_arp_projects(api_token: str) -> dict | None:
        """
        Make a call to the Schol-AR API to list all projects
        :return: JSON response from the API. None if failed response
        """
        url = 'https://www.Schol-AR.io/api/ListARP'
        headers = {'Authorization': f'Token {api_token}'}
        return APIManager.try_api_request(requests.get, True, url, headers=headers)

    @staticmethod
    def create_project(api_token: str, project_title: str, project_type: str, disc_url: str) -> dict | None:
        """
        Make a call to the Schol-AR API to create a new project
        :return: JSON response from the API. None if failed response
        """
        url = 'https://www.Schol-AR.io/api/CreateARP'
        headers = {
            'Authorization': f'Token {api_token}',
            # For some reason Schol-ar requires specifying this header with json content type to avoid an error
            'Content-Type': 'application/json'
        }
        data = {
            APIManager.PROJECT_TITLE_KEY: project_title,
            APIManager.PROJECT_TYPE_KEY: project_type,
            APIManager.PROJECT_DISC_URL_KEY: disc_url
        }
        return APIManager.try_api_request(requests.post, True, url, headers=headers, json=data)

    @staticmethod
    def get_qr_data(token: str, qr_string: str) -> dict | None:
        """
        Make call to API to retrieve cloud urls for qr code images
        :return: JSON response from the API. None if failed response
        """
        url = f'https://www.Schol-AR.io/api/GetQR/{qr_string}'
        headers = {'Authorization': f'Token {token}'}
        return APIManager.try_api_request(requests.get, True, url, headers=headers)

    @staticmethod
    def list_augs(api_token: str, qr_string: str) -> dict | None:
        """
        Make a call to the Schol-AR API to list all augmentations for a project
        :return: JSON response from the API. None if failed response
        """
        url = f'https://www.Schol-AR.io/api/ListAug/{qr_string}'
        headers = {'Authorization': f'Token {api_token}'}
        return APIManager.try_api_request(requests.get, True, url, headers=headers)

    @staticmethod
    def create_augmentation(
            token: str, qr_string: str, augmentation_title: str, augmentation_type: str) -> dict | None:
        """
        Make a call to the Schol-AR API to create a new augmentation
        :return: JSON response from the API. None if failed response
        """
        url = f'https://www.Schol-AR.io/api/CreateAug/{qr_string}'
        headers = {'Authorization': f'Token {token}'}
        data = {
            APIManager.AUGMENTATION_TITLE_KEY: augmentation_title,
            APIManager.AUGMENTATION_TYPE_KEY: augmentation_type,
        }
        return APIManager.try_api_request(requests.post, True, url, headers=headers, json=data)

    @staticmethod
    def edit_augmentation(token: str, qrstring: str, aug_id: str, file_path: str,
                          target_update: bool) -> dict | None:
        if not ScARFileManager.check_file_size(file_path):
            print(f"File size too large. Must be less than {APIManager.MAX_FILE_SIZE_MB}MB")
            return None

        url = f'https://www.Schol-AR.io/api/EditAug/{qrstring}/{aug_id}'
        headers = {'Authorization': f'Token {token}'}
        files = {}
        if target_update:
            files[APIManager.AUGMENTATION_TARGET_KEY] = open(file_path, 'rb')
        else:
            files[APIManager.AUGMENTATION_AUG_FILE_KEY] = open(file_path, 'rb')
        return APIManager.try_api_request(requests.patch, True, url, headers=headers, files=files)

    @staticmethod
    def download_file_from_url(url: str, save_dir: str):
        """
        Download a file from a URL and save it to a directory. File will be assigned name matching the name in the url.
        :param url: URL to download file from
        :param save_dir: what directory to download the file into
        """
        # Make a GET request to the URL
        response = requests.get(url)
        # Check if the request was successful
        if response.status_code == 200:
            # Extract the filename from the URL
            filename = APIManager.extract_filename_from_url(url)
            # Construct the full path where the file will be saved
            file_path = os.path.join(save_dir, filename)
            # Open a file in binary write mode
            with open(file_path, 'wb') as file:
                # Write the content of the response to the file
                file.write(response.content)
        else:
            print(f"Failed to download the file. Status code: {response.status_code}")

    @staticmethod
    def extract_filename_from_url(url: str) -> str:
        """
        Extract the filename from a cloud url
        :param url: Google cloud storage API URL
        :return: File name from url
        """
        parsed_url = urlparse(url)
        path = parsed_url.path
        filename = os.path.basename(path)

        # Protection against malicious file names

        # Remove or replace special characters
        sanitized_file_name = re.sub(r'[<>:"/\\|?*\x00-\x1F]', '_', filename)
        # Replace path traversal
        sanitized_file_name = re.sub(r'\.\.', '_', sanitized_file_name)
        # Replace absolute paths
        sanitized_file_name = re.sub(r'^[\\/]', '_', sanitized_file_name)
        return sanitized_file_name


class ScARFileManager:
    """
    All file management functionality for the Schol-AR CLI. This includes saving user data, projects, and augmentations.

    Manages the following file structure which is a slight adaptation of the Schol-AR API structure:

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
                - qr: Directory for qr codes
                    - pub: Directory for public qr codes
                    - admin: Directory for admin qr codes
    """
    BASE_DIR = os.path.join(app_dirs_unversioned.user_data_dir, "Schol-AR")

    USER_INFO_FILE = "users_info.json"
    USERS_INFO_PATH = os.path.join(BASE_DIR, USER_INFO_FILE)

    PROJECT_INFO_FILE = "projects_info.json"
    QR_DIR = "qr"
    AUGMENTATIONS_INFO_FILE = "augmentations_info.json"

    AUG_TARGET_IMAGE_DIR = "target_image"
    AUG_MODEL_DIR = "augmented_file"
    AUG_SESSION_DIR = "cxs"

    # used like a cache to avoid repeated file reads
    active_user_key = (None, None)

    @classmethod
    def username_exists(cls, username: str) -> bool:
        """
        Check if a username exists in the user_info.json file
        """
        users_info = cls.get_users_info()
        if users_info is None:
            return False
        return username in users_info.keys()

    @classmethod
    def project_exists(cls, username: str, project_title: str) -> bool:
        """
        Check if a project exists in the projects_info.json file
        """
        projects_info = cls.get_projects_info(username)
        if projects_info is None:
            return False
        return any(project.get(APIManager.PROJECT_TITLE_KEY) == project_title for project in projects_info)

    @classmethod
    def aug_exists(cls, username: str, project_title: str, augmentation_title: str) -> bool:
        """
        Check if an augmentation exists in the augmentations_info.json file
        """
        augmentations_info = cls.get_augs_info(username, project_title)
        if augmentations_info is None:
            return False
        return any(aug.get(APIManager.AUGMENTATION_TITLE_KEY) == augmentation_title for aug in augmentations_info)

    @classmethod
    def init_scholar_dirs(cls):
        """
        Initialize the user structure with a base directory and user_info.json file. Initialize the Schol-AR main
        directory if this is th first time a Schol-AR command is used.
        """

        # Define the path for the user_info.json file
        user_info_path = cls.USERS_INFO_PATH

        # Check if the user_info.json file already exists
        if not os.path.exists(user_info_path):
            # If it does not exist, create the initial structure of the JSON
            initial_data = {}

            # Ensure the base directory exists
            os.makedirs(cls.BASE_DIR, exist_ok=True)

            # Write the initial data to the user_info.json file
            with open(user_info_path, 'w') as file:
                json.dump(initial_data, file, indent=4)

    @classmethod
    def get_project_dir(cls, username: str, project_title: str) -> str:
        """
        Get (Create if doesn't already exist) the directory path for a specific project
        """
        project_dir = cls.get_project_dir_name(username, project_title)
        os.makedirs(project_dir, exist_ok=True)
        return project_dir

    @classmethod
    def get_project_dir_name(cls, username: str, project_title: str) -> str:
        """
        Get the directory path for a specific project
        """
        qr_string = cls.get_project_qrstring(username, project_title)
        project_dir = os.path.join(cls.BASE_DIR, username, qr_string)
        return project_dir

    @classmethod
    def get_aug_dir(cls, username: str, project_title: str, augmentation_title: str) -> str:
        """
        Get the directory path for a specific augmentation
        """
        aug_dir = cls.get_aug_dir_name(username, project_title, augmentation_title)
        os.makedirs(aug_dir, exist_ok=True)
        return aug_dir

    @classmethod
    def get_aug_dir_name(cls, username: str, project_title: str, augmentation_title: str) -> str:
        """
        Get the directory path for a specific augmentation
        """
        project_dir = cls.get_project_dir(username, project_title)
        aug_id = cls.get_augmentation_id(username, project_title, augmentation_title)
        aug_dir = os.path.join(project_dir, aug_id)
        return aug_dir

    @classmethod
    def update_users_info(cls, username: str, api_token: str):
        """
        Save/Update a user api token key value pair into a save file
        :param username: Username to add to the user save file. Must be validated first
        :param api_token: API token to add to the user save file. Must be validated first
        """
        # Get the current user info
        users_save_file = cls.get_users_info()

        users_save_file[username] = api_token

        # Write the updated user info back to the save file
        with open(cls.USERS_INFO_PATH, 'w') as file:
            json.dump(users_save_file, file, indent=4)

        # make sure directory for the user trying to log in exists
        user_dir = os.path.join(cls.BASE_DIR, username)
        os.makedirs(user_dir, exist_ok=True)

        cls.active_user_key = (username, api_token)

    @classmethod
    def get_user_token(cls, username: str) -> str | None:
        """
        Get the api token from a username out of the user save file otherwise return None
        """
        # avoid going through full file check if we keep asking the same user for the key
        active_user, active_key = cls.active_user_key
        if active_user == username:
            return active_key

        # the username does not match the "cached" name
        users_info = cls.get_users_info()
        if users_info is None:
            print("Failed to get user info save file to fetch user token")
            return None
        api_token = users_info.get(username)
        return api_token

    @classmethod
    def get_users_info(cls) -> dict | None:
        """
        :return: users save file as a json dictionary
        """
        # Check if the user_info.json file exists at the specified path
        if not os.path.exists(cls.USERS_INFO_PATH):
            # If the file does not exist, return None or an empty dictionary
            return None
        else:
            # If the file exists, open it and load the JSON data
            with open(cls.USERS_INFO_PATH, 'r') as file:
                users_info = json.load(file)
            return users_info

    @classmethod
    def get_projects_info_path(cls, username: str) -> str:
        """
        Get the path to the projects save file for a user
        """
        return os.path.join(cls.BASE_DIR, username, cls.PROJECT_INFO_FILE)

    @classmethod
    def get_projects_info(cls, username: str) -> dict | None:
        """
        :return: projects save file as a json dictionary
        """
        projects_info_path = cls.get_projects_info_path(username)

        # Check if the projects_info.json file exists
        if not os.path.exists(projects_info_path):
            return None

        # Open the projects_info.json file and load its contents
        with open(projects_info_path, 'r') as file:
            projects_info = json.load(file)

        return projects_info

    @classmethod
    def update_user_projects(cls, username: str):
        """
        API call and save response list of projects for a user into a save file.
        """
        if not cls.username_exists(username):
            return
        token = cls.get_user_token(username)
        list_arp_response = APIManager.list_arp_projects(token)
        if list_arp_response is None:
            print("Failed to retrieve user projects")
            return

        save_file_path = cls.get_projects_info_path(username)
        with open(save_file_path, 'w') as file:
            json.dump(list_arp_response, file, indent=4)

    @classmethod
    def get_project(cls, username: str, project_title: str) -> dict | None:
        """
        Retrieve a projects json data from the user's projects save file.
        :return: project json data or None if the project does not exist in the save file
        """
        if not cls.project_exists(username, project_title):
            return None
        projects_info = cls.get_projects_info(username)

        # Check if the project title exists in the list of projects and return the project data if found
        for project in projects_info:
            if project.get(APIManager.PROJECT_TITLE_KEY) == project_title:
                return project

        # If no matching project found, return None
        return None

    @classmethod
    def list_projects(cls, username: str) -> list:
        """
        :return: array of all existing project titles for a user
        """
        projects_info = cls.get_projects_info(username)
        if projects_info is None:
            return []

        return [project.get(APIManager.PROJECT_TITLE_KEY) for project in projects_info]

    @classmethod
    def get_project_qrstring(cls, username: str, project_title: str) -> str | None:
        """
        :return: QRString for a project or None if the project does not exist in the user's project save file
        """
        if not cls.project_exists(username, project_title):
            return None
        project = cls.get_project(username, project_title)
        return project.get(APIManager.PROJECT_QRSTRING_KEY)

    @classmethod
    def pub_qr_dir(cls, username: str, project_title: str) -> str:
        """
        Create the directory that the qr codes need to go into for a project
        :return: Path to the public qr code directory
        """
        project_dir = cls.get_project_dir(username, project_title)
        qr_dir = os.path.join(project_dir, cls.QR_DIR, "pub")
        os.makedirs(qr_dir, exist_ok=True)
        return qr_dir

    @classmethod
    def admin_qr_dir(cls, username: str, project_title: str) -> str:
        """
        Create the directory that the qr codes need to go into for a project
        :return: Path to the admin qr code directory
        """
        project_dir = cls.get_project_dir(username, project_title)
        qr_dir = os.path.join(project_dir, cls.QR_DIR, "admin")
        os.makedirs(qr_dir, exist_ok=True)
        return qr_dir

    @classmethod
    def get_qr_file(cls, username: str, project_title: str, admin: bool) -> str | None:
        """
        Get the full path to the qr code file for a project
        :return: Path to the qr code file or None if the project does not exist in the user's project save file
        """
        qr_dir = cls.admin_qr_dir(username, project_title) if admin else cls.pub_qr_dir(username, project_title)
        file_name = cls.get_first_file(qr_dir)
        if file_name is None:
            return None
        return os.path.join(qr_dir, file_name)

    @classmethod
    def update_augs_info(cls, username: str, project_title: str):
        """
        Make an API call that lists the augmentations for a project and update the projects save file.
        If the save file does not exist yet, create it.
        :param project_title: Title of a project that must exist in users project list.
        """
        if not cls.project_exists(username, project_title):
            return

        token = ScARFileManager.get_user_token(username)
        qrstring = ScARFileManager.get_project_qrstring(username, project_title)

        # update the project save file
        list_augs_response = APIManager.list_augs(token, qrstring)
        if list_augs_response is None:
            print(
                f"Failed to retrieve project augmentations to update for user: {username} project: {project_title}"
            )
            return

        # Construct the path to the project directory and ensure it exists
        project_dir_path = cls.get_project_dir(username, project_title)
        os.makedirs(project_dir_path, exist_ok=True)

        # Construct the path to the aug_info.json file within the project directory
        augs_info_path = os.path.join(project_dir_path, cls.AUGMENTATIONS_INFO_FILE)
        # Write the aug_info_data to the aug_info.json file
        with open(augs_info_path, 'w') as file:
            json.dump(list_augs_response, file, indent=4)

    @classmethod
    def init_aug_dirs(cls, username: str, project_title: str, augmentation_title: str, create_aug_response: dict):
        """
        Create the directory structure for the augmentation.
        """
        cls.aug_target_dir(username, project_title, augmentation_title)
        cls.aug_model_dir(username, project_title, augmentation_title)
        cls.aug_session_dir(username, project_title, augmentation_title)

    @classmethod
    def get_augmentation(cls, username: str, project_title: str, augmentation_title: str) -> dict | None:
        """
        :return: Json data for an augmentation or None if the augmentation does not exist in the project's augmentations
         save file
        """
        augmentations_info = cls.get_augs_info(username, project_title)

        # Check if the aug title exists in the list of augs and return the aug data if found
        for augmentation in augmentations_info:
            if augmentation.get(APIManager.AUGMENTATION_TITLE_KEY) == augmentation_title:
                return augmentation

        # If no matching augmentation, return None
        return None

    @classmethod
    def list_existing_aug_titles(cls, username: str, project_title: str) -> list:
        """
        :return: array of all existing augmentation titles for a project
        """
        augs_info = cls.get_augs_info(username, project_title)
        if augs_info is None:
            return []

        return [aug.get(APIManager.AUGMENTATION_TITLE_KEY) for aug in augs_info]

    @classmethod
    def get_augs_info(cls, username, project_title) -> dict | None:
        """
        :return: augmentations save file as a json dictionary
        """
        project_augmentations_dir = cls.get_project_dir(username, project_title)
        augs_info_path = os.path.join(project_augmentations_dir, cls.AUGMENTATIONS_INFO_FILE)

        # Check if the augs info save file exists
        if not os.path.exists(augs_info_path):
            return None

        # Open the augs info save file and load its contents
        with open(augs_info_path, 'r') as file:
            augmentations_info = json.load(file)

        return augmentations_info

    @classmethod
    def aug_target_dir(cls, username: str, project_title: str, augmentation_title: str) -> str:
        """
        Get (create if not existing) a full path for a standard aug target directory
        """
        base_aug_dir = cls.get_aug_dir(username, project_title, augmentation_title)
        target_dir = os.path.join(base_aug_dir, cls.AUG_TARGET_IMAGE_DIR)
        # trying to make the directory if it does not exist allows this to be used like a getter for the directory path
        # at times when it may not exist yet. Useful in the case of creating a new augmentation where files have to be
        # downloaded to create an augmentation.
        os.makedirs(target_dir, exist_ok=True)
        return target_dir

    @classmethod
    def aug_model_dir(cls, username: str, project_title: str, augmentation_title: str) -> str:
        """
        Get (create if not existing) a full path for a standard aug model directory
        """
        base_aug_dir = cls.get_aug_dir(username, project_title, augmentation_title)
        target_dir = os.path.join(base_aug_dir, cls.AUG_MODEL_DIR)
        os.makedirs(target_dir, exist_ok=True)
        return target_dir

    @classmethod
    def aug_session_dir(cls, username: str, project_title: str, augmentation_title: str) -> str:
        """
        Get (create if not existing) a full path for a standard aug session directory
        """
        base_aug_dir = cls.get_aug_dir(username, project_title, augmentation_title)
        target_dir = os.path.join(base_aug_dir, cls.AUG_SESSION_DIR)
        os.makedirs(target_dir, exist_ok=True)
        return target_dir

    @classmethod
    def aug_target_file(cls, username: str, project_title: str, augmentation_title: str) -> str:
        """
        Get (create if not existing) a full path for a standard aug target file
        """
        target_name = augmentation_title + "-target.png"
        return os.path.join(cls.aug_target_dir(username, project_title, augmentation_title), target_name)

    @classmethod
    def aug_model_file(cls, username: str, project_title: str, augmentation_title: str) -> str:
        """
        Get (create if not existing) a full path for a standard aug model file
        """
        model_name = augmentation_title + "-model.glb"
        return os.path.join(cls.aug_model_dir(username, project_title, augmentation_title), model_name)

    @classmethod
    def aug_session_file(cls, username: str, project_title: str, augmentation_title: str) -> str:
        """
        Get (create if not existing) a full path for a standard aug session file
        """
        session_name = augmentation_title + "-session.cxs"
        return os.path.join(cls.aug_session_dir(username, project_title, augmentation_title), session_name)

    @classmethod
    def get_augmentation_target_url(cls, username: str, project_title: str, augmentation_title: str) -> str | None:
        """
        :return: URL for the target image of an augmentation or None if the augmentation does not exist in the project's
        augmentations save file
        """
        aug = cls.get_augmentation(username, project_title, augmentation_title)
        return aug.get(APIManager.AUGMENTATION_TARGET_KEY)

    @classmethod
    def get_augmentation_model_url(cls, username: str, project_title: str, augmentation_title: str) -> str | None:
        """
        :return: URL for the augmented file of an augmentation or None if the augmentation does not exist in the
        project's augmentations save file
        """
        if not cls.aug_exists(username, project_title, augmentation_title):
            return None
        aug = cls.get_augmentation(username, project_title, augmentation_title)
        return aug.get(APIManager.AUGMENTATION_AUG_FILE_KEY)

    @classmethod
    def get_augmentation_id(cls, username, project_title, augmentation_title):
        aug = cls.get_augmentation(username, project_title, augmentation_title)
        return aug.get(APIManager.AUGMENTATION_INTERNAL_ID_KEY)

    @classmethod
    def get_aug_tracking_score(cls, username, project_title, augmentation_title):
        aug = cls.get_augmentation(username, project_title, augmentation_title)
        return aug.get(APIManager.AUGMENTATION_TRACKING_SCORE_KEY)

    @classmethod
    def get_augmentation_target_image_path(cls, username: str, project_title: str,
                                           augmentation_title: str) -> str | None:
        """
        Find and return the full path to the first file in the augmentation dir structure target image dir.
        If there is no file in that dir return none.
        """
        target_dir = cls.aug_target_dir(username, project_title, augmentation_title)
        first_file = cls.get_first_file(target_dir)
        if first_file:
            return os.path.join(target_dir, first_file)
        return None

    @classmethod
    def clean_local(cls, username: str):
        """
        Remove all project directories that are not located in the projects info file.
        """
        if not cls.username_exists(username):
            return

        # Make sure that the user's projects are up-to-date
        cls.update_user_projects(username)

        projects_info = cls.get_projects_info(username)
        if projects_info is None:
            return

        # collect an array of all expected project dir names from the save file.
        expected_project_dirs = [
            cls.get_project_dir_name(username, project[APIManager.PROJECT_TITLE_KEY]) for project in projects_info
        ]
        user_base_dir = os.path.join(cls.BASE_DIR, username)

        # iterate through all the dirs in the user's base dir and remove any that are not an expected name
        for item in os.listdir(user_base_dir):
            item_path = os.path.join(user_base_dir, item)
            if os.path.isdir(item_path) and item_path not in expected_project_dirs:
                shutil.rmtree(item_path)

        # For each project, update the augmentations and clean up augmentation directories
        for project in projects_info:
            project_title = project[APIManager.PROJECT_TITLE_KEY]
            cls.update_augs_info(username, project_title)

            augmentations_info = cls.get_augs_info(username, project_title)
            if augmentations_info is None:
                continue

            # Collect an array of all expected augmentation dir names from the save file
            expected_aug_dirs = [
                cls.get_aug_dir_name(username, project_title, aug[APIManager.AUGMENTATION_TITLE_KEY]) for aug in
                augmentations_info
            ]
            project_dir = cls.get_project_dir(username, project_title)

            # Iterate through all the aug dirs in the project dir and remove any that are not an expected aug name
            for item in os.listdir(project_dir):
                item_path = os.path.join(project_dir, item)
                if os.path.isdir(item_path) and item_path not in expected_aug_dirs:
                    shutil.rmtree(item_path)


    @classmethod
    def empty_dir(cls, file_for_delete):
        """
        Remove all files in a directory
        """
        for file in os.listdir(file_for_delete):
            file_path = os.path.join(file_for_delete, file)
            os.remove(file_path)

    @classmethod
    def path_exists(cls, path):
        """
        :return: True if the path exists, False if it does not
        """
        if path is None:
            return False
        full_path = os.path.expanduser(path)
        return os.path.exists(full_path)

    @classmethod
    def save_file_copy(cls, file_for_copy: str, destination_dir: str):
        """
        Save a copy of a file to a directory. All params must be validated before calling this method.
        :param file_for_copy: Full path to the file that needs ot be copied
        :param destination_dir: Directory to copy file into
        """
        # support ~ in file paths
        full_file_for_copy_path = os.path.expanduser(file_for_copy)
        full_destination_dir = os.path.expanduser(destination_dir)

        # Extract the filename from the full path
        filename = os.path.basename(full_file_for_copy_path)
        # Construct the full path for the destination file
        destination_file_path = os.path.join(full_destination_dir, filename)
        # Copy the file to the destination
        shutil.copy(full_file_for_copy_path, destination_file_path)

    @classmethod
    def get_first_file(cls, search_dir: str) -> str | None:
        """
        Get the first file name in a directory. If the directory is empty, return None.
        :param search_dir: A directory that exists.
        :return: The name of the first file found in the directory, or None if the directory is empty.
        """
        # Attempt to list all items in the specified directory
        try:
            files = os.listdir(search_dir)
            # Filter out directories, leaving only files
            files = [file for file in files if
                     (os.path.isfile(os.path.join(search_dir, file)) and not file.startswith('.'))]
            if files:
                return files[0]  # Return the first file found
            else:
                return None  # Return None if no files are found
        except Exception as e:
            return None

    @classmethod
    def check_file_size(cls, file_path: str, max_size: int = APIManager.MAX_FILE_SIZE_MB) -> bool:
        """
        Check if a file is less than a certain size.
        :param file_path: Path to the file to check
        :param max_size: Maximum size in Mb
        :return: True if the file is less than the max size, False if it is equal to or greater than the max size. False
        if the path does not lead to a file.
        """
        if not os.path.isfile(file_path):
            return False

        file_size = os.path.getsize(file_path) / (1024 * 1024)  # Convert bytes to megabytes
        return file_size < max_size
