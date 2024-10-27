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


"""
This module provides ChimeraX commands for managing user login, project selection, and augmentation within the
Schol-AR application.
"""

import os.path
import shutil
from typing import Union

from chimerax.core.commands import CmdDesc, StringArg, BoolArg, SaveFileNameArg, SaveFolderNameArg, OpenFileNameArg
from chimerax.core.commands import run

from . import api_manager
from . import sc_file_manager
from .utils import empty_dir, get_first_file, path_exists, save_file_copy


def login(session, username: str, api_token: Union[str, None] = None, **kwargs):
    """
    ChimeraX command that is used to log in a Schol-AR chimerax user. If the user does not exist, the user's name and
    Schol-AR API token will be saved together into a save file that is used to keep track of all users. If the user
    already exists, this command will update the user's project info save file. Once the user is created in the dir
    structure, network call the Schol-AR side for the user's projects.

    :param session: The current ChimeraX session.
    :param username: The username of the Schol-AR user.
    :param api_token: The API token for the Schol-AR user. If None, the token will be retrieved from the save file.
    """
    if not valid_input_string(username):
        session.logger.warning("Invalid username. Usernames can only contain letters, numbers, and spaces.")
        return

    sc_file_manager.init_scholar_dirs()
    user_token = api_token
    if user_token is None:
        # cmd call has implied that user already exists
        retrieved_token = sc_file_manager.get_user_token(username)
        if retrieved_token is None:
            # if the user did not exist in the info file
            session.logger.warning(f"User {username} does not exist")
            return
        user_token = retrieved_token

    if not api_manager.validate_api_token(user_token):
        # exit on invalid api token
        session.logger.warning(f"Invalid API token for: {username}")
        return

    sc_file_manager.update_users_info(username, user_token)

    sc_file_manager.update_user_projects(username)
    session.logger.status("Succesfully logged into Schol-AR as: " + username)


login_desc = CmdDesc(
    self_logging=True,
    required=[('username', StringArg)],
    optional=[('api_token', StringArg)],
    synopsis="Store Username and API Token for Schol-AR"
)


def project(session, username: str, project_title: str, project_type: str = "other", disc_url: str = ""):
    """
    ChimeraX command that is used to set up the directory structure and augmentation info save file for a project. If
    the project already exists, its augmentation save file will be updated, otherwise a new project will be created on
    Schol-AR and then the directory structure and augmentation save file will be generated.

    :param session: The current ChimeraX session.
    :param username: The username of the Schol-AR user.
    :param project_title: The title of the project.
    :param project_type: The type of the project. Default is "other".
    :param disc_url: The URL for the project description. Default is an empty string.
    """
    if not username_exists(username):
        return

    if not valid_input_string(project_title):
        session.logger.warning("Invalid project title. Project titles can only contain letters, numbers, and spaces.")
        return

    if project_type not in api_manager.PROJECT_TYPES.values():
        project_types = ", ".join(api_manager.PROJECT_TYPES.values())
        session.logger.warning(f"Invalid project type. Project type must be one of: {project_types}")
        return

    # set target project if param project_title exists in the user's project list. None means it does not exist
    target_project: dict = sc_file_manager.get_project(username, project_title)

    if target_project is None:
        # The project does not exist in the user's project list
        # create the project on server
        token = sc_file_manager.get_user_token(username)
        project_response = api_manager.create_project(token, project_title, project_type, disc_url)
        if project_response is None:
            # this will happen if there is a network call error
            session.logger.warning(f"Failed to create project: {project_title} on scholar server")
            return

        # create the project locally
        sc_file_manager.update_user_projects(username)

        # now that the project is created try setting again
        target_project = sc_file_manager.get_project(username, project_title)

        # if the target_project is still none that means that there was an error creating the project locally
        if target_project is None:
            session.logger.error(f"Failed to create project locally {project_title}")
            return

    # Once we get to here we know that the project exists in the user's project list and qr dirs
    sc_file_manager.update_augs_info(username, project_title)


project_desc = CmdDesc(
    required=[('username', StringArg),
              ('project_title', StringArg)],
    optional=[('project_type', StringArg),
              ('disc_url', StringArg)],
    synopsis="Create a new project on Schol-AR"
)


def download_qr(session, username: str, project_title: str):
    """
    ChimeraX command to download the QR code .png files for a project.

    :param session: The current ChimeraX session.
    :param username: The username of the Schol-AR user.
    :param project_title: The title of the project.
    """
    if not usr_project_exists(username, project_title):
        return

    qrstring = sc_file_manager.get_project_qrstring(username, project_title)
    token = sc_file_manager.get_user_token(username)
    qr_data = api_manager.get_qr_data(token, qrstring)

    if qr_data is None:
        session.logger.warning(f"Failed to download project files for project {project_title}")
        return

    pub_save_dir = sc_file_manager.pub_qr_dir(username, project_title)
    admin_save_dir = sc_file_manager.admin_qr_dir(username, project_title)

    # if the qr code ever changes name for some reason or if there are extra files floating around this will clean up
    empty_dir(pub_save_dir)
    empty_dir(admin_save_dir)

    api_manager.download_file_from_url(qr_data[api_manager.PUBLIC_QR_KEY], pub_save_dir)
    api_manager.download_file_from_url(qr_data[api_manager.ADMIN_QR_KEY], admin_save_dir)


download_qr_desc = CmdDesc(
    required=[('username', StringArg),
              ('project_title', StringArg)],
    synopsis="Download qr codes for a project"
)


def augmentation(session, username: str, project_title: str, augmentation_title: str, augmentation_type: str = 'model',
                 verbose: bool = False):
    """
    ChimeraX command that is used to prepare an augmentation to be able to download associated files. This command
    can be used to select an existing augmentation from Schol-AR remote data to set up the local directory structure,
    or it can be used to make a new augmentation. If a new augmentation is created on Schol-AR, the project info save
    file will be updated to reflect the new augmentation. The new augmentation made on the Schol-AR end will
    initially be blank. Immediately after creating a new augmentation, the target image and augmented file will be
    uploaded to the Schol-AR server that reflect whatever the current session is set to.

    :param session: The current ChimeraX session.
    :param username: The username of the Schol-AR user.
    :param project_title: The title of the project.
    :param augmentation_title: The title of the augmentation.
    :param augmentation_type: The type of the augmentation. Default is 'model'. Only supported type is 'model'.
    :param verbose: If True, the command will log additional information. Default is False.
    """
    if not usr_project_exists(username, project_title):
        return

    if not valid_input_string(augmentation_title):
        session.logger.warning("Invalid augmentation title. Augmentation titles can contain only letters, numbers, and "
                               "spaces.")
        return

    if augmentation_type != "model":
        session.logger.warning("Invalid augmentation type. Only supported augmentation type is 'model'.")
        return

    # check if the aug needs to be created or if it exists in the project info save file
    target_aug_data = sc_file_manager.get_augmentation(username, project_title, augmentation_title)
    if target_aug_data is None:
        # The augmentation does not exist yet

        token = sc_file_manager.get_user_token(username)
        qrstring = sc_file_manager.get_project_qrstring(username, project_title)

        # check if the model and target image files are too large before creating the augmentation
        if not sc_file_manager.save_and_size_check(session, '.glb'):
            session.logger.warning(f"Model file must be smaller than {api_manager.MAX_FILE_SIZE_MB}MB. "
                                   f"Reduce model detail and try again.")
            session.logger.warning("Could not create new augmentation.")
            return
        if not sc_file_manager.save_and_size_check(session, '.png'):
            session.logger.warning(f"Target Image file must be smaller than {api_manager.MAX_FILE_SIZE_MB}MB.")
            session.logger.warning("Could not create new augmentation.")
            return

        # The augmentation needs to be created on Schol-AR side.
        create_aug_response = api_manager.create_augmentation(
            token, qrstring, augmentation_title, augmentation_type
        )

        # Check to see if anything went wrong with the network post
        if create_aug_response is None:
            session.logger.warning(f"Failed to create augmentation {augmentation_title} for project {project_title}")
            return

        # update the project save file once we know the augmentation was created
        sc_file_manager.update_augs_info(username, project_title)

        # refresh the target augmentation. Pulls from newly updated project info
        target_aug_data = sc_file_manager.get_augmentation(username, project_title, augmentation_title)

        # This needs to happen before we try and upload the files to the server because we need to save them into the
        # directory structure
        sc_file_manager.init_aug_dirs(username, project_title, augmentation_title, target_aug_data)

        run(session,
            f"scholar uploadAugFiles \"{username}\" \"{project_title}\" \"{augmentation_title}\" target_image True "
            f"augmented_file True verbose {verbose}"
            , log=verbose)

    else:
        # the augmentation already exists in the project info save file
        # make sure the dir structure for the augmentation is set up
        sc_file_manager.init_aug_dirs(username, project_title, augmentation_title, target_aug_data)


augmentation_desc = CmdDesc(
    required=[('username', StringArg),
              ('project_title', StringArg),
              ('augmentation_title', StringArg)],
    keyword=[('augmentation_type', StringArg),
             ('verbose', BoolArg)],
    synopsis="Create a new augmentation for a project"
)


def download_aug_files(
        session, username: str, project_title: str, augmentation_title: str,
        target_image: bool = True, augmented_file: bool = False):
    """
    ChimeraX command to sync selected files for an augmentation to the local directory structure. This command is
    used to download the augmentation files into the Schol-AR directory structure.

    :param session: The current ChimeraX session.
    :param username: The username of the Schol-AR user.
    :param project_title: The title of the project.
    :param augmentation_title: The title of the augmentation.
    :param target_image: If True, the target image will be downloaded. Default is True.
    :param augmented_file: If True, the augmented file will be downloaded. Default is False.
    """
    if not usr_proj_aug_exists(username, project_title, augmentation_title):
        return

    if target_image:
        target_image_url = sc_file_manager.get_augmentation_target_url(username, project_title, augmentation_title)

        # check if the target image exists
        if target_image_url is None:
            session.logger.warning(f"Can't sync because Target Image for: {augmentation_title} not found")
        else:
            # only keep the 1 file that is being used
            target_dir = sc_file_manager.aug_target_dir(username, project_title, augmentation_title)
            empty_dir(target_dir)

            target_image_save_path = sc_file_manager.aug_target_dir(username, project_title, augmentation_title)
            api_manager.download_file_from_url(target_image_url, target_image_save_path)

    if augmented_file:
        augmented_url = sc_file_manager.get_augmentation_model_url(username, project_title, augmentation_title)
        # check if the augmented file exists
        if augmented_url is None:
            session.logger.warning(f"Can't sync because Augmented File for: {augmentation_title} not found")
        else:
            # only keep the 1 file that is being used in the directory
            model_dir = sc_file_manager.aug_model_dir(username, project_title, augmentation_title)
            empty_dir(model_dir)

            augmented_save_path = sc_file_manager.aug_model_dir(username, project_title, augmentation_title)
            api_manager.download_file_from_url(augmented_url, augmented_save_path)


download_aug_files_desc = CmdDesc(
    required=[('username', StringArg),
              ('project_title', StringArg),
              ('augmentation_title', StringArg)],
    keyword=[('target_image', BoolArg),
             ('augmented_file', BoolArg),
             ('verbose', BoolArg)],
    synopsis="Download augmentation files"
)


def upload_aug_files(session, username: str, project_title: str, augmentation_title: str,
                     target_image: bool = False, augmented_file: bool = True, verbose: bool = False):
    """
    ChimeraX command to sync local files to the remote directory structure. This command is used to upload the
    selected augmentation files into the Schol-AR directory structure.

    :param session: The current ChimeraX session.
    :param username: The username of the Schol-AR user.
    :param project_title: The title of the project.
    :param augmentation_title: The title of the augmentation.
    :param target_image: If True, the target image will be uploaded. Default is False.
    :param augmented_file: If True, the augmented file will be uploaded. Default is True.
    :param verbose: If True, the command will log additional information. Default is False.
    """
    if not usr_proj_aug_exists(username, project_title, augmentation_title):
        return

    token = sc_file_manager.get_user_token(username)

    # it is important that augmented file gets patched before the target image does. As of 07/30/24 schol-ar has a bug
    # where if the target image is updated directly before the model it will get stuck displayed as processing.
    if augmented_file:
        model_dir = sc_file_manager.aug_model_dir(username, project_title, augmentation_title)
        empty_dir(model_dir)
        model_file = sc_file_manager.aug_model_file(username, project_title, augmentation_title)
        aug_save_and_update(session, token, username, project_title, augmentation_title, model_file,
                            target_update=False, verbose=verbose)
    if target_image:
        target_image_dir = sc_file_manager.aug_target_dir(username, project_title, augmentation_title)
        empty_dir(target_image_dir)
        target_image_file = sc_file_manager.aug_target_file(username, project_title, augmentation_title)
        aug_save_and_update(session, token, username, project_title, augmentation_title, target_image_file,
                            target_update=True, verbose=verbose)


upload_aug_files_desc = CmdDesc(
    required=[('username', StringArg),
              ('project_title', StringArg),
              ('augmentation_title', StringArg)],
    keyword=[('target_image', BoolArg),
             ('augmented_file', BoolArg),
             ('verbose', BoolArg)],
    synopsis="Upload augmentation files"
)


def aug_save_and_update(session, token: str, username: str, project_title: str, augmentation_title: str,
                        file_path: str, target_update: bool, verbose: bool = False):
    """
    Save and update Schol-AR with one file.

    :param session: The current ChimeraX session.
    :param token: The API token for the Schol-AR user.
    :param username: The username of the Schol-AR user.
    :param project_title: The title of the project.
    :param augmentation_title: The title of the augmentation.
    :param file_path: The path to the file that will be saved. Contains file type extension for the save command.
    :param target_update: If True, update the target image. If False, update the augmented file.
    :param verbose: If True, the command will log additional information. Default is False.
    """
    qrstring = sc_file_manager.get_project_qrstring(username, project_title)
    aug_id = sc_file_manager.get_augmentation_id(username, project_title, augmentation_title)
    # save the file to local directory
    run(session, f"save \"{file_path}\"", log=verbose)
    # update the augmentation on the server
    updated_aug_info = api_manager.edit_augmentation(
        token, qrstring, aug_id, file_path, target_update=target_update
    )
    # something on the server failed check
    if updated_aug_info is None:
        field_target = "target image" if target_update else "augmented file"
        session.logger.warning(f"Failed to upload augmentation {field_target} for {augmentation_title} in project "
                               f"{project_title}")
        return
    # make sure that the save files for the project are updated
    sc_file_manager.update_augs_info(username, project_title)


def save_aug_session(session, username: str, project_title: str, augmentation_title: str,
                     file_path: Union[str, None] = None, verbose: bool = False):
    """
    ChimeraX command to save a .cxs session file to the augmentation's directory. The session file will be saved/copied
    into the augmentation's directory.

    :param session: The current ChimeraX session.
    :param username: The username of the Schol-AR user.
    :param project_title: The title of the project.
    :param augmentation_title: The title of the augmentation.
    :param file_path: Path to a target .cxs file to save. If None or doesn't exist, the current session will be saved.
    :param verbose: If True, the command will log additional information. Default is False.
    """
    if not usr_proj_aug_exists(username, project_title, augmentation_title):
        return

    aug_session_dir = sc_file_manager.aug_session_dir(username, project_title, augmentation_title)

    # if the file path is not valid, save the existing session to the augmentation and set the target session path
    if file_path is None or not path_exists(file_path):
        target_session_file = sc_file_manager.aug_session_file(username, project_title, augmentation_title)
        # empty the directory before saving the session
        empty_dir(aug_session_dir)
        run(session, f"save \"{target_session_file}\"", log=verbose)
    else:
        # Valid session file given from outside Schol-AR dir structure. Copy the file to the augmentation session dir.
        empty_dir(aug_session_dir)
        save_file_copy(file_path, aug_session_dir)


save_aug_session_desc = CmdDesc(
    required=[('username', StringArg),
              ('project_title', StringArg),
              ('augmentation_title', StringArg)],
    keyword=[('file_path', OpenFileNameArg),
             ('verbose', BoolArg)],
    synopsis="Save a session file to the augmentation"
)


def open_aug_session(session, username: str, project_title: str, augmentation_title: str, verbose: bool = False):
    """
    ChimeraX command to open a .cxs session file from the augmentation's directory. Assumes that there is only
    one session file stored at a time per augmentation. If there are multiple session files, the first listed one will
    be opened.

    :param session: The current ChimeraX session.
    :param username: The username of the Schol-AR user.
    :param project_title: The title of the project.
    :param augmentation_title: The title of the augmentation.
    :param verbose: If True, the command will log additional information. Default is False.
    """
    if not usr_proj_aug_exists(username, project_title, augmentation_title):
        return

    aug_session_dir = sc_file_manager.aug_session_dir(username, project_title, augmentation_title)
    session_file_name = get_first_file(aug_session_dir)
    if session_file_name is None:
        session.logger.info(f"No session file yet for Augmentation: {augmentation_title}")
        return

    open_session_path = os.path.join(aug_session_dir, session_file_name)
    run(session, f"open \"{open_session_path}\"", log=verbose)


open_aug_session_desc = CmdDesc(
    required=[('username', StringArg),
              ('project_title', StringArg),
              ('augmentation_title', StringArg)],
    keyword=[('verbose', BoolArg)],
    synopsis="Open a session file from the augmentation"
)


def store_target_image(session, username: str, project_title: str, augmentation_title: str, save_location: str,
                       verbose: bool = False):
    """
    ChimeraX command to save the target image to a location outside the Schol-AR directory structure.

    :param session: The current ChimeraX session.
    :param username: The username of the Schol-AR user.
    :param project_title: The title of the project.
    :param augmentation_title: The title of the augmentation.
    :param save_location: The location to save the target image.
    :param verbose: If True, the command will log additional information. Default is False.
    """
    if not usr_proj_aug_exists(username, project_title, augmentation_title):
        return

    target_image_path = sc_file_manager.get_augmentation_target_image_path(username, project_title, augmentation_title)
    if target_image_path is None:
        run(session,
            f"scholar downloadAugFiles \"{username}\" \"{project_title}\" \"{augmentation_title}\" "
            f"targetImage True augmentedFile False", log=verbose)
        target_image_path = sc_file_manager.get_augmentation_target_image_path(
            username, project_title, augmentation_title)

    if target_image_path is not None:
        # if the target image path exists, and the save directory exists, copy the file
        shutil.copyfile(target_image_path, format_file_extension(save_location, ".png"))


store_target_image_desc = CmdDesc(
    required=[('username', StringArg),
              ('project_title', StringArg),
              ('augmentation_title', StringArg),
              ('save_location', SaveFileNameArg)],
    keyword=[('verbose', BoolArg)],
    synopsis="Save the target image to a location outside the Schol-AR directory structure"
)


def store_model(session, username: str, project_title: str, augmentation_title: str, save_location: str,
                verbose: bool = False):
    """
    ChimeraX command to save the augmented model to a location outside the Schol-AR directory structure.

    :param session: The current ChimeraX session.
    :param username: The username of the Schol-AR user.
    :param project_title: The title of the project.
    :param augmentation_title: The title of the augmentation.
    :param save_location: The location to save the augmented model.
    :param verbose: If True, the command will log additional information. Default is False.
    """
    if not usr_proj_aug_exists(username, project_title, augmentation_title):
        return

    model_path = sc_file_manager.get_auggmentation_model_file_path(username, project_title, augmentation_title)
    if model_path is None:
        run(session, f"scholar downloadAugFiles \"{username}\" \"{project_title}\" \"{augmentation_title}\" "
                     f"targetImage False augmentedFile True", log=verbose)
        model_path = sc_file_manager.get_auggmentation_model_file_path(username, project_title, augmentation_title)

    if model_path is not None:
        # if the model path exists, and the save directory exists, copy the file
        shutil.copyfile(model_path, format_file_extension(save_location, ".glb"))


store_model_desc = CmdDesc(
    required=[('username', StringArg),
              ('project_title', StringArg),
              ('augmentation_title', StringArg),
              ('save_location', SaveFileNameArg)],
    keyword=[('verbose', BoolArg)],
    synopsis="Save the augmented model to a location outside the Schol-AR directory structure"
)


def store_all_aug_files(session, username: str, project_title: str, augmentation_title: str, save_folder: str,
                        verbose: bool = False):
    """
    ChimeraX command to save all the augmentation files and QR code to a location outside the Schol-AR directory
    structure.

    :param session: The current ChimeraX session.
    :param username: The username of the Schol-AR user.
    :param project_title: The title of the project.
    :param augmentation_title: The title of the augmentation.
    :param save_folder: The folder to save all the augmentation files.
    :param verbose: If True, the command will log additional information. Default is False.
    """
    if not usr_proj_aug_exists(username, project_title, augmentation_title):
        return
    os.makedirs(save_folder, exist_ok=True)
    safe_aug_filename = api_manager.sanitize_file_name(augmentation_title)
    model_file_path = os.path.join(save_folder, f"{safe_aug_filename}.glb")
    target_image_file_path = os.path.join(save_folder, f"{safe_aug_filename}.png")
    # Use the project title as the qr image file name. The qr title is a unique identifier and is confusing.
    qr_image_file_path = os.path.join(save_folder, f"{project_title}_qr.png")
    run(session, f"scholar storeModel \"{username}\" \"{project_title}\" \"{augmentation_title}\" "
                 f"\"{model_file_path}\"", log=verbose)
    run(session, f"scholar storeTargetImage \"{username}\" \"{project_title}\" \"{augmentation_title}\" "
                 f"\"{target_image_file_path}\"", log=verbose)
    run(session, f"scholar storeQR \"{username}\" \"{project_title}\" \"{qr_image_file_path}\"", log=verbose)


store_all_aug_files_desc = CmdDesc(
    required=[('username', StringArg),
              ('project_title', StringArg),
              ('augmentation_title', StringArg),
              ('save_folder', SaveFolderNameArg)],
    keyword=[('verbose', BoolArg)],
    synopsis="Save all augmentation files to a location outside the Schol-AR directory structure"
)


def store_qr_image(session, username: str, project_title: str, save_location: str, verbose: bool = False):
    """
    ChimeraX command to save the public QR code image to a location outside the Schol-AR directory structure.

    :param session: The current ChimeraX session.
    :param username: The username of the Schol-AR user.
    :param project_title: The title of the project.
    :param save_location: The location to save the QR code image.
    :param verbose: If True, the command will log additional information. Default is False.
    """
    if not usr_project_exists(username, project_title):
        return

    pub_qr_image_path = sc_file_manager.get_qr_file(username, project_title, admin=False)
    if pub_qr_image_path is None:
        run(session, f"scholar downloadQR \"{username}\" \"{project_title}\"", log=verbose)
        pub_qr_image_path = sc_file_manager.get_qr_file(username, project_title, admin=False)

    if pub_qr_image_path is not None:
        # if the public QR code image path exists, and the save directory exists, copy the file
        shutil.copyfile(pub_qr_image_path, format_file_extension(save_location, ".png"))


store_qr_image_desc = CmdDesc(
    required=[('username', StringArg),
              ('project_title', StringArg),
              ('save_location', SaveFileNameArg)],
    keyword=[('verbose', BoolArg)],
    synopsis="Save the public QR code image to a location outside the Schol-AR directory structure"
)


def format_file_extension(file_path: str, file_extension):
    """
    Ensure that a file path has the desired file extension. The extension must be a valid extension with a period.

    :param file_path: The path to the file.
    :param file_extension: The desired file extension, including the period (e.g., ".png").
    :return: The file path with the desired extension.
    """
    if not file_path.endswith(file_extension):
        return file_path + file_extension
    return file_path


def clean_local(session, username: str = None):
    """
    ChimeraX command to clean all the local files that are associated with projects or augmentations that no longer
    exist on Schol-AR remote. A username can be specified to target which user the files are deleted for. If no username
    is specified, all users' files will be cleaned.

    :param session: The current ChimeraX session.
    :param username: The username of the Schol-AR user.
    """
    target_usernames = [username]

    if username is None:
        target_usernames = sc_file_manager.list_usernames()
    elif not username_exists(username):
        session.logger.warning(f"Cannot Clean Local. User {username} not found")
        return

    for username in target_usernames:
        sc_file_manager.clean_local(username)


clean_local_desc = CmdDesc(
    optional=[('username', StringArg)],
    synopsis="Clean all local files that are associated with projects or augmentations that no longer exist on Schol-AR"
)


def remove_user(session, username: str):
    """
    ChimeraX command to remove a user from the Schol-AR directory structure. This command will remove the user's
    directory and all associated projects and augmentations.

    :param session: The current ChimeraX session.
    :param username: The username of the Schol-AR user.
    """

    if sc_file_manager.remove_user(username):
        session.logger.info(f"User {username} removed")
        return
    session.logger.warning(f"Can't remove user {username} because it was not found")


remove_user_desc = CmdDesc(
    required=[('username', StringArg)],
    synopsis="Remove a user from the Schol-AR directory structure"
)


def username_exists(username: str):
    """
    Check if a username is mapped to a valid api token.

    :param username: The username to check.
    :return: True if the username exists, False otherwise.
    """
    # make sure the user exists
    if not sc_file_manager.username_exists(username):
        print(f"User {username} not found")
        return False
    return True


def usr_project_exists(username: str, project_title: str):
    """
    Check if a project exists for a given user.

    :param username: The username of the Schol-AR user.
    :param project_title: The title of the project to check.
    :return: True if the project exists, False otherwise.
    """
    # make sure the user and project exist
    if not username_exists(username):
        return False
    if not sc_file_manager.project_exists(username, project_title):
        print(f"Project {project_title} not found")
        return False
    return True


def usr_proj_aug_exists(username: str, project_title: str, augmentation_title: str):
    """
    Check if an augmentation exists for a given project and user.

    :param username: The username of the Schol-AR user.
    :param project_title: The title of the project.
    :param augmentation_title: The title of the augmentation to check.
    :return: True if the augmentation exists, False otherwise.
    """
    # make sure the user, project, and augmentation exist
    if not usr_project_exists(username, project_title):
        return False
    if not sc_file_manager.aug_exists(username, project_title, augmentation_title):
        print(f"Augmentation {augmentation_title} not found")
        return False
    return True


def valid_input_string(input_string: str):
    """
    Validate that an input string contains only letters, numbers, and spaces, and is not empty.

    :param input_string: The string to validate.
    :return: True if the string is valid, False otherwise.
    """
    if input_string is None or input_string == "":
        return False
    return all(char.isalnum() or char.isspace() for char in input_string)
