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
import shutil
from typing import Optional

MAX_FILE_SIZE_MB = 30


def check_file_size(file_path: str, max_size: int = MAX_FILE_SIZE_MB) -> bool:
    """
    Check if the file size is within the allowed limit.

    :param file_path: The path to the file to check.
    :return: True if the file size is within the allowed limit, False otherwise.
    """
    if not os.path.isfile(file_path):
        return False

    file_size = os.path.getsize(file_path) / (1024 * 1024)  # Convert bytes to megabytes
    return file_size < max_size


def empty_dir(file_for_delete):
    """
    Empty the contents of a directory without deleting the directory itself.

    :param dir_path: The path to the directory to empty.
    """
    for file in os.listdir(file_for_delete):
        file_path = os.path.join(file_for_delete, file)
        os.remove(file_path)


def path_exists(path):
    """
    Check if a given path exists.

    :param path: The path to check.
    :return: True if the path exists, False otherwise.
    """
    if path is None:
        return False
    full_path = os.path.expanduser(path)
    return os.path.exists(full_path)


def save_file_copy(file_for_copy: str, destination_dir: str):
    """
    Save a copy of a file to a directory. All parameters must be validated before calling this method.

    :param file_for_copy: Full path to the file that needs to be copied.
    :param destination_dir: Directory to copy the file into.
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


def get_first_file(search_dir: str) -> Optional[str]:
    """
    Get the first file in a directory.

    :param dir_path: The path to the directory to search.
    :return: The name of the first file found, or None if the directory is empty.
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
