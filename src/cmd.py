import os.path
import shutil

from chimerax.core.commands import CmdDesc, StringArg, BoolArg, SaveFileNameArg, SaveFolderNameArg
from chimerax.core.commands import run

from .io import ScARFileManager, APIManager


def login(session, username: str, api_token: str | None = None):
    """
    ChimeraX command that is used to log in a Schol-AR chimerax user. If the user does not exist, the users name and
    Schol-AR api token will be saved together into a save file that is used to keep track of all users. If the user
    already exists, this command will update the user's project info save file. Once the user is created in the dir
    structure, network call the Schol-AR side for the users projects.
    """

    if not valid_input_string(username):
        session.logger.info("Invalid username. Usernames can only contain letters, numbers, and spaces.")
        return

    ScARFileManager.init_scholar_dirs()
    user_token = api_token
    if user_token is None:
        # cmd call has implied that user already exists
        retrieved_token = ScARFileManager.get_user_token(username)
        if retrieved_token is None:
            # if the user did not exist in the info file
            session.logger.info(f"User {username} does not exist")
            return
        user_token = retrieved_token

    if not APIManager.validate_api_token(user_token):
        # exit on invalid api token
        session.logger.info(f"Invalid API token: {user_token}")
        return

    ScARFileManager.update_users_info(username, user_token)

    ScARFileManager.update_user_projects(username)


login_desc = CmdDesc(
    required=[('username', StringArg)],
    optional=[('api_token', StringArg)],
    synopsis="Store Username and API Token for Schol-AR"
)


def project(session, username: str, project_title: str, project_type: str = "other", disc_url: str = ""):
    """
    ChimeraX command that is used to set up the directory structure and augmentation info save file for a project. If
    the project already exists, it's augmentation save file will be updated, otherwise a new project will be created on
    Schol-AR and then the directory struct and augmentation save file will be generated.
    """

    if not username_exists(username):
        return

    if not valid_input_string(project_title):
        session.logger.info("Invalid project title. Project titles can only contain letters, numbers, and spaces.")
        return

    # set target project if param project_title exists in the user's project list. None means it does not exist
    target_project: dict = ScARFileManager.get_project(username, project_title)

    if target_project is None:
        # The project does not exist in the user's project list
        # create the project on server
        token = ScARFileManager.get_user_token(username)
        project_response = APIManager.create_project(token, project_title, project_type, disc_url)
        if project_response is None:
            # this will happen if there is a network call error
            session.logger.info(f"Failed to create project: {project_title} on scholar server")
            return

        # create the project locally
        ScARFileManager.update_user_projects(username)

        # now that the project is created try setting again
        target_project = ScARFileManager.get_project(username, project_title)

        # if the target_project is still none that means that there was an error creating the project locally
        if target_project is None:
            session.logger.info(f"Failed to create project locally {project_title}")
            return

    # Once we get to here we know that the project exists in the user's project list and qr dirs
    ScARFileManager.update_augs_info(username, project_title)


project_desc = CmdDesc(
    required=[('username', StringArg),
              ('project_title', StringArg)],
    optional=[('project_type', StringArg),
              ('disc_url', StringArg)],
    synopsis="Create a new project on Schol-AR"
)


def download_qr(session, username: str, project_title: str):
    """
    ChimeraX command to download the qr codes for a project.
    """

    if not usr_project_exists(username, project_title):
        return

    qrstring = ScARFileManager.get_project_qrstring(username, project_title)
    token = ScARFileManager.get_user_token(username)
    qr_data = APIManager.get_qr_data(token, qrstring)

    if qr_data is None:
        session.logger.info(f"Failed to download project files for project {project_title}")
        return

    pub_save_dir = ScARFileManager.pub_qr_dir(username, project_title)
    admin_save_dir = ScARFileManager.admin_qr_dir(username, project_title)

    # if the qr code ever changes name for some reason or if there are extra files floating around this will clean up
    ScARFileManager.empty_dir(pub_save_dir)
    ScARFileManager.empty_dir(admin_save_dir)

    APIManager.download_file_from_url(qr_data[APIManager.PUBLIC_QR_KEY], pub_save_dir)
    APIManager.download_file_from_url(qr_data[APIManager.ADMIN_QR_KEY], admin_save_dir)


download_qr_desc = CmdDesc(
    required=[('username', StringArg),
              ('project_title', StringArg)],
    synopsis="Download qr codes for a project"
)


def augmentation(session, username: str, project_title: str, augmentation_title: str, augmentation_type: str = 'model'):
    """
    ChimeraX command that is used to prepare an augmentation to be able to download associated files. This
    Command can be used to select an existing augmentation from Schol-AR remote data to set up the local directory
    structure, or it can be used to make a new augmentation. If a new augmentation is created the project info save file
    will be updated to reflect the new augmentation. The new projcet made on the scholar end will initially be blank.
    Immediately after creating a new augmentation, the target image and augmented file will be uploaded to the Schol-AR
    server that reflect whatever the current session is set to.
    """

    if not usr_project_exists(username, project_title):
        return

    if not valid_input_string(augmentation_title):
        session.logger.info("Invalid augmentation title. Augmentation titles can contain only letters, numbers, and "
                            "spaces.")
        return

    # check if the aug needs to be created or if it exists in the project info save file
    target_aug_data = ScARFileManager.get_augmentation(username, project_title, augmentation_title)
    if target_aug_data is None:
        # The augmentation does not exist yet

        token = ScARFileManager.get_user_token(username)
        qrstring = ScARFileManager.get_project_qrstring(username, project_title)

        # The augmentation needs to be created on Schol-AR side.
        create_aug_response = APIManager.create_augmentation(
            token, qrstring, augmentation_title, augmentation_type
        )

        # Check to see if anything went wrong with the network post
        if create_aug_response is None:
            session.logger.info(f"Failed to create augmentation {augmentation_title} for project {project_title}")
            return

        # update the project save file once we know the augmentation was created
        ScARFileManager.update_augs_info(username, project_title)

        # refresh the target augmentation. Pulls from newly updated project info
        target_aug_data = ScARFileManager.get_augmentation(username, project_title, augmentation_title)

        # This needs to happen before we try and upload the files to the server because we need to save them into the
        # directory structure
        ScARFileManager.init_aug_dirs(username, project_title, augmentation_title, target_aug_data)

        run(session,
            f"scholar uploadAugFiles \"{username}\" \"{project_title}\" \"{augmentation_title}\" target_image True "
            f"augmented_file True"
            )

    else:
        # the augmentation already exists in the project info save file
        # make sure the dir structure for the augmentation is set up
        ScARFileManager.init_aug_dirs(username, project_title, augmentation_title, target_aug_data)


augmentation_desc = CmdDesc(
    required=[('username', StringArg),
              ('project_title', StringArg),
              ('augmentation_title', StringArg)],
    keyword=[('augmentation_type', StringArg)],
    synopsis="Create a new augmentation for a project"
)


def download_aug_files(
        session, username: str, project_title: str, augmentation_title: str,
        target_image: bool = True, augmented_file: bool = False):
    """
    ChimeraX command to sync selected files for an augmentation to the local directory structure. This command is
    used to download the augmentation files into the setup directory structure.
    """

    if not usr_proj_aug_exists(username, project_title, augmentation_title):
        return

    if target_image:
        target_image_url = ScARFileManager.get_augmentation_target_url(username, project_title, augmentation_title)

        # check if the target image exists
        if target_image_url is None:
            session.logger.info(f"Can't sync because Target Image for: {augmentation_title} not found")
        else:
            # only keep the 1 file that is being used
            target_dir = ScARFileManager.aug_target_dir(username, project_title, augmentation_title)
            ScARFileManager.empty_dir(target_dir)

            target_image_save_path = ScARFileManager.aug_target_dir(username, project_title, augmentation_title)
            APIManager.download_file_from_url(target_image_url, target_image_save_path)

    if augmented_file:
        augmented_url = ScARFileManager.get_augmentation_model_url(username, project_title, augmentation_title)
        # check if the augmented file exists
        if augmented_url is None:
            session.logger.info(f"Can't sync because Augmented File for: {augmentation_title} not found")
        else:
            # only keep the 1 file that is being used in the directory
            model_dir = ScARFileManager.aug_model_dir(username, project_title, augmentation_title)
            ScARFileManager.empty_dir(model_dir)

            augmented_save_path = ScARFileManager.aug_model_dir(username, project_title, augmentation_title)
            APIManager.download_file_from_url(augmented_url, augmented_save_path)


download_aug_files_desc = CmdDesc(
    required=[('username', StringArg),
              ('project_title', StringArg),
              ('augmentation_title', StringArg)],
    keyword=[('target_image', BoolArg),
             ('augmented_file', BoolArg)],
    synopsis="Download augmentation files"
)


def upload_aug_files(session, username: str, project_title: str, augmentation_title: str,
                     target_image: bool = False, augmented_file: bool = True):
    """
    ChimeraX command to sync local files to the remote directory structure. This command is used to upload the
    selected augmentation files into the Schol-AR directory structure.
    """

    if not usr_proj_aug_exists(username, project_title, augmentation_title):
        return

    token = ScARFileManager.get_user_token(username)

    # it is important that augmented file gets patched before the target image does. As of 07/30/24 schol-ar has a bug
    # where if the target image is updated directly before the model it will get stuck displayed as processing.
    if augmented_file:
        model_dir = ScARFileManager.aug_model_dir(username, project_title, augmentation_title)
        ScARFileManager.empty_dir(model_dir)
        model_file = ScARFileManager.aug_model_file(username, project_title, augmentation_title)
        aug_save_and_update(session, token, username, project_title, augmentation_title, model_file,
                            target_update=False)
    if target_image:
        target_image_dir = ScARFileManager.aug_target_dir(username, project_title, augmentation_title)
        ScARFileManager.empty_dir(target_image_dir)
        target_image_file = ScARFileManager.aug_target_file(username, project_title, augmentation_title)
        aug_save_and_update(session, token, username, project_title, augmentation_title, target_image_file,
                            target_update=True)


upload_aug_files_desc = CmdDesc(
    required=[('username', StringArg),
              ('project_title', StringArg),
              ('augmentation_title', StringArg)],
    keyword=[('target_image', BoolArg),
             ('augmented_file', BoolArg)],
    synopsis="Upload augmentation files"
)


def aug_save_and_update(session, token: str, username: str, project_title: str, augmentation_title: str,
                        file_path: str, target_update: bool):
    """
    Save and update scholar with one file
    :param file_path: the path to the file that will be saved. Contains file type extension for the save command.
    :param target_update: if true update the target image, if false update the augmented file
    """
    qrstring = ScARFileManager.get_project_qrstring(username, project_title)
    aug_id = ScARFileManager.get_augmentation_id(username, project_title, augmentation_title)
    # save the file to local directory
    run(session, f"save \"{file_path}\"")
    # update the augmentation on the server
    updated_aug_info = APIManager.edit_augmentation(
        token, qrstring, aug_id, file_path, target_update=target_update
    )
    # something on the server failed check
    if updated_aug_info is None:
        session.logger.info(f"Failed to update augmentation {augmentation_title} for project {project_title}")
        return
    # make sure that the save files for the project are updated
    ScARFileManager.update_augs_info(username, project_title)


def save_aug_session(session, username: str, project_title: str, augmentation_title: str, file_path: str | None = None):
    """
    ChimeraX command to save a .cxs session file to the augmentation's directory.
    :param file_path: Path to a target .cxs file to save. If None or doesn't exist, the current session will be saved.
    """

    if not usr_proj_aug_exists(username, project_title, augmentation_title):
        return

    aug_session_dir = ScARFileManager.aug_session_dir(username, project_title, augmentation_title)

    # if the file path is not valid, save the existing session to the augmentation and set the target session path
    if file_path is None or not ScARFileManager.path_exists(file_path):
        target_session_file = ScARFileManager.aug_session_file(username, project_title, augmentation_title)
        # empty the directory before saving the session
        ScARFileManager.empty_dir(aug_session_dir)
        run(session, f"save \"{target_session_file}\"")
    else:
        # Valid session file given from outside Schol-AR dir structure. Copy the file to the augmentation session dir.
        ScARFileManager.empty_dir(aug_session_dir)
        ScARFileManager.save_file_copy(file_path, aug_session_dir)


save_aug_session_desc = CmdDesc(
    required=[('username', StringArg),
              ('project_title', StringArg),
              ('augmentation_title', StringArg)],
    keyword=[('file_path', StringArg)],
    synopsis="Save a session file to the augmentation"
)


def open_aug_session(session, username: str, project_title: str, augmentation_title: str):
    """
    ChimeraX command to open a .cxs session file from the augmentation's directory. Assumes that there is only
    one session file stored at a time per augmentation. If there are multiple session files, the first listed one will
    be opened.
    """

    if not usr_proj_aug_exists(username, project_title, augmentation_title):
        return

    aug_session_dir = ScARFileManager.aug_session_dir(username, project_title, augmentation_title)
    session_file_name = ScARFileManager.get_first_file(aug_session_dir)
    if session_file_name is None:
        session.logger.info(f"No session file found for Augmentation: {augmentation_title}")
        return

    open_session_path = os.path.join(aug_session_dir, session_file_name)
    run(session, f"open \"{open_session_path}\"")


open_aug_session_desc = CmdDesc(
    required=[('username', StringArg),
              ('project_title', StringArg),
              ('augmentation_title', StringArg)],
    synopsis="Open a session file from the augmentation"
)


def store_target_image(session, username: str, project_title: str, augmentation_title: str, save_location: str):
    """
    ChimeraX command to save the target image to a location outside the Schol-AR directory structure.
    """

    if not usr_proj_aug_exists(username, project_title, augmentation_title):
        return

    target_image_path = ScARFileManager.get_augmentation_target_image_path(username, project_title, augmentation_title)
    if target_image_path is None:
        run(session,
            f"scholar downloadAugFiles \"{username}\" \"{project_title}\" \"{augmentation_title}\" targetImage True augmentedFile False")
        target_image_path = ScARFileManager.get_augmentation_target_image_path(
            username, project_title, augmentation_title)

    if target_image_path is not None:
        # if the target image path exists, and the save directory exists, copy the file
        shutil.copyfile(target_image_path, format_file_extension(save_location, ".png"))


store_target_image_desc = CmdDesc(
    required=[('username', StringArg),
              ('project_title', StringArg),
              ('augmentation_title', StringArg),
              ('save_location', SaveFileNameArg)],
    synopsis="Save the target image to a location outside the Schol-AR directory structure"
)


def store_model(session, username: str, project_title: str, augmentation_title: str, save_location: str):
    """
    ChimeraX command to save the augmented model to a location outside the Schol-AR directory structure.
    """

    if not usr_proj_aug_exists(username, project_title, augmentation_title):
        return

    model_path = ScARFileManager.get_auggmentation_model_file_path(username, project_title, augmentation_title)
    if model_path is None:
        run(session, f"scholar downloadAugFiles \"{username}\" \"{project_title}\" \"{augmentation_title}\" "
                     f"targetImage False augmentedFile True")
        model_path = ScARFileManager.get_auggmentation_model_file_path(username, project_title, augmentation_title)

    if model_path is not None:
        # if the model path exists, and the save directory exists, copy the file
        shutil.copyfile(model_path, format_file_extension(save_location, ".glb"))


store_model_desc = CmdDesc(
    required=[('username', StringArg),
              ('project_title', StringArg),
              ('augmentation_title', StringArg),
              ('save_location', SaveFileNameArg)],
    synopsis="Save the augmented model to a location outside the Schol-AR directory structure"
)


def store_all_aug_files(session, username: str, project_title: str, augmentation_title: str, save_folder: str):
    """
    ChimeraX command to save all the augmentation files to a location outside the Schol-AR directory structure.
    """

    if not usr_proj_aug_exists(username, project_title, augmentation_title):
        return
    os.makedirs(save_folder, exist_ok=True)
    safe_aug_filename = APIManager.sanitize_file_name(augmentation_title)
    model_file_path = os.path.join(save_folder, f"{safe_aug_filename}.glb")
    target_image_file_path = os.path.join(save_folder, f"{safe_aug_filename}.png")
    run(session, f"scholar storeModel \"{username}\" \"{project_title}\" \"{augmentation_title}\" "
                 f"\"{model_file_path}\"")
    run(session, f"scholar storeTargetImage \"{username}\" \"{project_title}\" \"{augmentation_title}\" "
                 f"\"{target_image_file_path}\"")


store_all_aug_files_desc = CmdDesc(
    required=[('username', StringArg),
              ('project_title', StringArg),
              ('augmentation_title', StringArg),
              ('save_folder', SaveFolderNameArg)],
    synopsis="Save all augmentation files to a location outside the Schol-AR directory structure"
)


def store_qr_image(session, username: str, project_title: str, save_location: str):
    """
    ChimeraX command to save the public QR code image to a location outside the Schol-AR directory structure.
    """

    if not usr_project_exists(username, project_title):
        return

    pub_qr_image_path = ScARFileManager.get_qr_file(username, project_title, admin=False)
    if pub_qr_image_path is None:
        run(session, f"scholar downloadQR \"{username}\" \"{project_title}\"")
        pub_qr_image_path = ScARFileManager.get_qr_file(username, project_title, admin=False)

    if pub_qr_image_path is not None:
        # if the public QR code image path exists, and the save directory exists, copy the file
        shutil.copyfile(pub_qr_image_path, format_file_extension(save_location, ".png"))


store_qr_image_desc = CmdDesc(
    required=[('username', StringArg),
              ('project_title', StringArg),
              ('save_location', SaveFileNameArg)],
    synopsis="Save the public QR code image to a location outside the Schol-AR directory structure"
)


def format_file_extension(file_path: str, file_extension):
    """
    Ensure that a file path has the desired file extension. The extension must be a valid extension with a period.
    """
    if not file_path.endswith(file_extension):
        return file_path + file_extension
    return file_path


def clean_local(session, username: str):
    """
    ChimeraX command to clean all the local files that are associated with projects or augmentations that no longer
    exist on Schol-AR relmote.
    """

    if not username_exists(username):
        return

    ScARFileManager.clean_local(username)


clean_local_desc = CmdDesc(
    required=[('username', StringArg)],
    synopsis="Clean all local files that are associated with projects or augmentations that no longer exist on Schol-AR"
)


def username_exists(username: str):
    # make sure the user exists
    if not ScARFileManager.username_exists(username):
        print(f"User {username} not found")
        return False
    return True


def usr_project_exists(username: str, project_title: str):
    # make sure the user and project exist
    if not username_exists(username):
        return False
    if not ScARFileManager.project_exists(username, project_title):
        print(f"Project {project_title} not found")
        return False
    return True


def usr_proj_aug_exists(username: str, project_title: str, augmentation_title: str):
    # make sure the user, project, and augmentation exist
    if not usr_project_exists(username, project_title):
        return False
    if not ScARFileManager.aug_exists(username, project_title, augmentation_title):
        print(f"Augmentation {augmentation_title} not found")
        return False
    return True


def valid_input_string(input_string: str):
    """
    All user inputted strings need to only contain letters, numbers, and spaces. In addition, they cannot be empty.
    """
    if input_string is None or input_string == "":
        return False
    return all(char.isalnum() or char.isspace() for char in input_string)
