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


from chimerax.core.commands import register
from chimerax.core.toolshed import BundleAPI

from . import cmd
from . import tool


class _MyAPI(BundleAPI):
    api_version = 1

    # Override method
    @staticmethod
    def start_tool(session, bi, ti):
        """
        This method is called once for each time the tool is invoked.

        :param session: an instance of chimerax.core.session.Session
        :param bi: an instance of chimerax.core.toolshed.BundleInfo
        :param ti: an instance of chimerax.core.toolshed.ToolInfo
        :return: an instance of tool.ChimeraXScholARTool if the tool name matches the bundle short name
        :raises ValueError: if trying to start an unknown tool
        """

        # Implies that the bundle name is the same as the name in classifiers in bundle_info.xml
        if ti.name == bi.short_name:
            return tool.ChimeraXScholARTool(session, ti.name)
        raise ValueError("trying to start unknown tool: %s" % ti.name)

    @staticmethod
    def get_class(class_name):
        # class_name will be a string
        if class_name == tool.ChimeraXScholARTool.__name__:
            return tool.ChimeraXScholARTool
        raise ValueError("Unknown class name '%s'" % class_name)

    @staticmethod
    def register_command(bi, ci, logger):
        # bi is an instance of chimerax.core.toolshed.BundleInfo
        # ci is an instance of chimerax.core.toolshed.CommandInfo
        # logger is an instance of chimerax.core.logger.Logger

        if ci.name == "scholar login":
            func = cmd.login
            desc = cmd.login_desc
        elif ci.name == "scholar project":
            func = cmd.project
            desc = cmd.project_desc
        elif ci.name == "scholar augmentation":
            func = cmd.augmentation
            desc = cmd.augmentation_desc
        elif ci.name == "scholar downloadAugFiles":
            func = cmd.download_aug_files
            desc = cmd.download_aug_files_desc
        elif ci.name == "scholar uploadAugFiles":
            func = cmd.upload_aug_files
            desc = cmd.upload_aug_files_desc
        elif ci.name == "scholar downloadQR":
            func = cmd.download_qr
            desc = cmd.download_qr_desc
        elif ci.name == "scholar saveAugSession":
            func = cmd.save_aug_session
            desc = cmd.save_aug_session_desc
        elif ci.name == "scholar openAugSession":
            func = cmd.open_aug_session
            desc = cmd.open_aug_session_desc
        elif ci.name == "scholar storeTargetImage":
            func = cmd.store_target_image
            desc = cmd.store_target_image_desc
        elif ci.name == "scholar storeModel":
            func = cmd.store_model
            desc = cmd.store_model_desc
        elif ci.name == "scholar storeAllAugFiles":
            func = cmd.store_all_aug_files
            desc = cmd.store_all_aug_files_desc
        elif ci.name == "scholar storeQRImage":
            func = cmd.store_qr_image
            desc = cmd.store_qr_image_desc
        elif ci.name == "scholar cleanLocal":
            func = cmd.clean_local
            desc = cmd.clean_local_desc
        elif ci.name == "scholar removeUser":
            func = cmd.remove_user
            desc = cmd.remove_user_desc
        else:
            raise ValueError("trying to register unknown command: %s" % ci.name)

        register(ci.name, desc, func)

    @staticmethod
    def initialize(session, bundle_info):
        from . import api_manager
        api_manager.logger = session.logger


# Create the ``bundle_api`` object that ChimeraX expects.
bundle_api = _MyAPI()
