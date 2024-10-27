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
This module contains the implementation of the Scholar UI components for the Scholar application.

Classes:
    ScholarAugPreviewWidget: Widget for previewing augmentations within a project.
    ScholarLoginWidget: Widget for handling user login within the Scholar application.
    ScholarProjectWidget: Widget for handling project selection and creation within the Scholar application.
    ScholarSelAugWidget: Widget for selecting and creating augmentations within a project.
    ScholarAugEditWidget: Widget for editing augmentations within a project.
    ScholarMainLayout: Main layout for the Scholar application, managing different widgets for login, project selection,
                       augmentation selection, and augmentation editing.
"""

import os

from Qt.QtCore import Qt, QUrl
from Qt.QtGui import QPixmap, QDesktopServices
from Qt.QtWidgets import (QFrame, QVBoxLayout, QWidget, QComboBox, QFormLayout, QLabel, QLineEdit,
                          QPushButton, QHBoxLayout, QStackedLayout, QSizePolicy)

from .api_manager import PROJECT_TYPES


class ScholarAugPreviewWidget(QWidget):
    """
    Widget for previewing augmentations within a project.

    This widget provides a user interface to display the target image, public QR code,
    admin QR code, and the tracking score for an augmentation. It also allows assigning
    the preview to a tool window.
    """

    def __init__(self):
        """
        Initialize the ScholarAugPreviewWidget.
        """
        super().__init__()
        self.setup_aug_preview_ui()

    def setup_aug_preview_ui(self):
        """
        Set up the UI for the augmentation preview widget.
        """
        self.layout = QVBoxLayout(self)

        # Create a horizontal layout to the preview label and the label stack for the qr and tracking score
        self.h_layout = QHBoxLayout()

        # left vertical stack
        self.left_v_layout = QVBoxLayout()

        # Main preview label
        self.previewLabel = QLabel()
        self.previewLabel.setAlignment(Qt.AlignCenter)
        self.left_v_layout.addWidget(self.previewLabel)

        # tracking score label
        self.tracking_score_label = QLabel("Tracking Score: 0/5")

        # Support links in the tracking score label.
        self.tracking_score_label.setOpenExternalLinks(True)
        self.tracking_score_label.setTextFormat(Qt.TextFormat.RichText)

        self.left_v_layout.addWidget(self.tracking_score_label)

        self.h_layout.addLayout(self.left_v_layout)

        # Right vertical stack
        self.right_v_layout = QVBoxLayout()

        # Directions label
        self.directions_label = QLabel()
        self.directions_label.setWordWrap(True)
        self.directions_label.setTextFormat(Qt.TextFormat.RichText)
        self.directions_label.setOpenExternalLinks(True)
        self.directions_label.setText(
            'Aim your mobile device at the QR code to load augmentations. Once loaded aim the mobile device at the '
            'target image to see augmentations. <a href="https://www.schol-ar.io/overview/">[Overview]</a>'
        )
        self.directions_label.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Preferred)
        self.directions_label.setMinimumSize(400, 50)  # Set a minimum size to prevent it from shrinking too much
        self.right_v_layout.addWidget(self.directions_label)

        self.pub_qr_h_layout = QHBoxLayout()

        self.pub_qr_left_stack = QVBoxLayout()

        self.pub_qr_title_label = QLabel("Public QR")
        self.pub_qr_title_label.setAlignment(Qt.AlignCenter)
        self.pub_qr_left_stack.addWidget(self.pub_qr_title_label)

        # QR code labels for pixmap
        self.pub_qr_label = QLabel()
        self.pub_qr_label.setFixedSize(150, 150)
        self.pub_qr_label.setAlignment(Qt.AlignCenter)
        self.pub_qr_left_stack.addWidget(self.pub_qr_label)

        self.pub_qr_h_layout.addLayout(self.pub_qr_left_stack)
        # Public QR code directions
        self.pub_qr_dirs_label = QLabel()
        self.pub_qr_dirs_label.setWordWrap(True)
        self.pub_qr_dirs_label.setMinimumWidth(200)
        self.pub_qr_dirs_label.setText(
            "Use this QR in your publication/project to allow anyone to see the augmented content. This QR is "
            "permanent. This QR will work when scanned from your normal camera app or from within the Schol-AR app."
        )
        self.pub_qr_h_layout.addWidget(self.pub_qr_dirs_label)

        self.right_v_layout.addLayout(self.pub_qr_h_layout)

        self.admin_qr_h_layout = QHBoxLayout()

        self.admin_qr_left_stack = QVBoxLayout()

        self.admin_qr_title_label = QLabel("Private QR")
        self.admin_qr_title_label.setAlignment(Qt.AlignCenter)
        self.admin_qr_left_stack.addWidget(self.admin_qr_title_label)

        # Admin QR code labels for pixmap
        self.admin_qr_label = QLabel()
        self.admin_qr_label.setFixedSize(150, 150)
        self.admin_qr_label.setAlignment(Qt.AlignCenter)
        self.admin_qr_left_stack.addWidget(self.admin_qr_label)

        self.admin_qr_h_layout.addLayout(self.admin_qr_left_stack)

        # Admin QR code directions
        self.admin_qr_dirs_label = QLabel()
        self.admin_qr_dirs_label.setWordWrap(True)
        self.admin_qr_dirs_label.setMinimumWidth(200)
        self.admin_qr_dirs_label.setTextFormat(Qt.TextFormat.RichText)
        self.admin_qr_dirs_label.setOpenExternalLinks(True)
        self.admin_qr_dirs_label.setText(
            "You can edit your augmentations with this QR. This QR is not permanent, do not give it to anyone. It is "
            "your 'password' to edit your project and it may become inactive or change. This QR will only work when "
            "scanned through the Schol-AR App. <a href=\"https://www.schol-ar.io/intro/\">[Details]</a>"
        )

        self.admin_qr_h_layout.addWidget(self.admin_qr_dirs_label)

        self.right_v_layout.addLayout(self.admin_qr_h_layout)

        # Add the vertical layout containing the QR label to the horizontal layout
        self.h_layout.addLayout(self.right_v_layout)

        # Add the horizontal layout to the main layout
        self.layout.addLayout(self.h_layout)

        # Set the alignment of the main layout to top left
        self.layout.setAlignment(Qt.AlignTop | Qt.AlignLeft)

        self.setLayout(self.layout)

    @staticmethod
    def create_new_aug_preview_ui(child_window, target_image_path, pub_qr_path, admin_qr_path, tracking_score):
        """
        Create a new augmentation preview UI.

        :param child_window: The child window to assign the preview UI to.
        :param target_image_path: The path to the target image.
        :param pub_qr_path: The path to the public QR code image.
        :param admin_qr_path: The path to the admin QR code image.
        :param tracking_score: The target image tracking score.
        """
        preview_widget = ScholarAugPreviewWidget()
        preview_widget.assign_to_preview_window(child_window)
        preview_widget.preview_aug(target_image_path, pub_qr_path, admin_qr_path, tracking_score)

    def preview_aug(self, preview_image_path, pub_qr_path, admin_qr_path, tracking_score):
        """
        Preview the augmentation.

        :param preview_image_path: The path to the preview image.
        :param pub_qr_path: The path to the public QR code image.
        :param admin_qr_path: The path to the admin QR code image.
        :param tracking_score: The tracking score.
        """
        preview_pixmap = QPixmap(preview_image_path)
        self.previewLabel.setPixmap(
            preview_pixmap.scaled(self.previewLabel.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation)
        )

        if tracking_score < 0:
            self.tracking_score_label.setText(f"Try refreshing in a moment for Tracking Score.")
        elif tracking_score < 30:
            self.tracking_score_label.setText(f"Tracking Score: {int(tracking_score//20)}/5 Image tracking may be acceptable "
                                              f"but could be improved. <a href=\"https://www.schol-ar.io/AugImages"
                                              f"\">[Info]</a>")
        else:
            self.tracking_score_label.setText(f"Tracking Score: {int(tracking_score//20)}/5")

        pub_qr_pixmap = QPixmap(pub_qr_path)
        self.pub_qr_label.setPixmap(
            pub_qr_pixmap.scaled(self.pub_qr_label.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation)
        )

        admin_qr_pixmap = QPixmap(admin_qr_path)
        self.admin_qr_label.setPixmap(
            admin_qr_pixmap.scaled(self.admin_qr_label.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation))

    def assign_to_preview_window(self, tool_window):
        """
        Assign the preview widget to a tool window.

        :param tool_window: The tool window to assign the preview widget to.
        """
        # This needs to be called before preview_aug is called so that the layout is set and the window size can pick up
        # on the right sizeHints
        tool_window.setLayout(self.layout)


class ScholarLoginWidget(QWidget):
    """
    Widget for handling user login within the Scholar application.
    """

    def __init__(self):
        """
        Initialize the ScholarLoginWidget.
        """
        super().__init__()
        self.setup_ui()

    def setup_ui(self):
        """
        Set up the UI for the login widget.
        """
        self.main_layout = QVBoxLayout(self)
        # This spacing will apply to all sub layouts
        self.main_layout.setSpacing(10)

        # Horizontal layout to split the tool info image + message and the existing user login form layout
        self.info_and_existing_user = QHBoxLayout()

        # Horizontal layout for image and message
        self.info_layout = QHBoxLayout()

        # Image for the tool info
        self.tool_info_image = QLabel()
        self.tool_info_image.setMaximumWidth(100)
        info_im_path = os.path.join(os.path.dirname(__file__), 'resources', 'images', 'scholarimage.png')
        info_pixmap = QPixmap(info_im_path)
        self.tool_info_image.setPixmap(info_pixmap.scaled(self.tool_info_image.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation))
        self.info_layout.addWidget(self.tool_info_image)

        # Message for the tool info
        self.tool_info_text = QLabel()
        self.tool_info_text.setWordWrap(True)
        self.tool_info_text.setTextFormat(Qt.TextFormat.RichText)
        self.tool_info_text.setOpenExternalLinks(True)
        self.tool_info_text.setText(
            'Schol-AR enables the embedding of 3D models and other digital media directly in publications & posters. '
            '<a href="https://www.schol-ar.io/overview/">[Overview here]</a>')
        self.tool_info_text.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        self.tool_info_text.setMinimumWidth(120)
        self.info_layout.addWidget(self.tool_info_text)

        self.info_and_existing_user.addLayout(self.info_layout)

        # form layout for existing user selection
        self.existing_user_selection_layout = QFormLayout()
        self.existing_user_selection_layout.setFieldGrowthPolicy(QFormLayout.AllNonFixedFieldsGrow)
        self.existing_user_selection_layout.setSpacing(5)

        self.existing_user_label = QLabel("Existing User:")
        self.existing_user_combobox = QComboBox()

        self.existing_user_selection_layout.addRow(self.existing_user_label, self.existing_user_combobox)

        # add the existing user form hbox to the info-existing user hbox layout. Put it into a v box to bottom align
        self.existing_user_vbox = QVBoxLayout()
        self.existing_user_vbox.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.existing_user_vbox.setSpacing(0)
        self.existing_user_vbox.addLayout(self.existing_user_selection_layout)

        # Submit button for existing user
        self.select_existing_user_button = QPushButton("Select Existing User")
        self.select_existing_user_button.adjustSize()
        self.existing_user_vbox.addWidget(self.select_existing_user_button, alignment=Qt.AlignmentFlag.AlignRight)

        self.info_and_existing_user.addLayout(self.existing_user_vbox)

        # add the info and existing user form hbox to main layout
        self.main_layout.addLayout(self.info_and_existing_user)

        # Create new user label
        self.new_user_label = QLabel("Create New User")
        self.main_layout.addWidget(self.new_user_label, alignment=Qt.AlignmentFlag.AlignCenter)

        # New User Form
        self.new_user_layout = QFormLayout()
        self.new_user_layout.setFieldGrowthPolicy(QFormLayout.AllNonFixedFieldsGrow)
        self.new_user_layout.setSpacing(5)

        self.user_label = QLabel("Username:")
        self.user_lineedit = QLineEdit()

        self.api_token_label = QLabel("API Token:")
        self.api_token_lineedit = QLineEdit()

        self.new_user_layout.addRow(self.user_label, self.user_lineedit)
        self.new_user_layout.addRow(self.api_token_label, self.api_token_lineedit)

        self.main_layout.addLayout(self.new_user_layout)

        # API Key Directions and submit button layout
        self.bottom_submission_hbox = QHBoxLayout()
        self.bottom_submission_hbox.setSpacing(30)


        # API Key Directions
        self.api_key_directions = QLabel()
        self.api_key_directions.setWordWrap(True)
        self.api_key_directions.setTextFormat(Qt.TextFormat.RichText)
        self.api_key_directions.setOpenExternalLinks(True)
        self.api_key_directions.setText(
            'To get an API token, first <a href="https://www.schol-ar.io/register/">sign up</a> and <a '
            'href="https://www.schol-ar.io/login/">log in</a> (free).'
            'Second click profile and then Get API Token.'
        )
        self.api_key_directions.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        # calculate the min height required for the label to wrap text to a second line
        font_metrics = self.api_key_directions.fontMetrics()
        line_height = font_metrics.lineSpacing()
        min_height = line_height * 2
        self.api_key_directions.setMinimumHeight(min_height)
        self.bottom_submission_hbox.addWidget(self.api_key_directions)

        # Submit button for new user
        self.submit_new_user_button = QPushButton("Submit")
        self.submit_new_user_button.adjustSize()
        self.submit_new_user_button.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Fixed)
        self.bottom_submission_hbox.addWidget(self.submit_new_user_button, alignment=Qt.AlignmentFlag.AlignRight)

        self.main_layout.addLayout(self.bottom_submission_hbox)

    def refresh_iu(self):
        """
        Refresh the input fields for the login widget.
        """
        self.existing_user_combobox.clear()
        self.user_lineedit.clear()
        self.api_token_lineedit.clear()

    def set_login_combobox(self, users: list):
        """
        Set the items in the existing user combobox.

        :param users: List of usernames to add to the combobox.
        """
        self.existing_user_combobox.clear()
        self.existing_user_combobox.addItems(users)

    def get_exiting_user(self) -> str:
        """
        Get the selected existing user.

        :return: The username of the selected existing user.
        """
        return self.existing_user_combobox.currentText()

    def get_new_login_info(self) -> tuple:
        """
        Get the new login information.

        :return: A tuple containing the username and API token.
        """
        return self.user_lineedit.text(), self.api_token_lineedit.text()

    @property
    def new_user_signal(self):
        """
        Signal for the new user submission button.

        :return: The clicked signal of the submit new user button.
        """
        return self.submit_new_user_button.clicked

    @property
    def existing_user_signal(self):
        """
        Signal for the existing user selection button.

        :return: The clicked signal of the select existing user button.
        """
        return self.select_existing_user_button.clicked


class ScholarProjectWidget(QWidget):
    """
    Widget for handling Schol-AR project selection and creation.
    """

    def __init__(self):
        """
        Initialize the ScholarProjectWidget.
        """
        super().__init__()
        self.setup_ui()

    def setup_ui(self):
        """
        Set up the UI for the project widget.
        """
        self.main_layout = QVBoxLayout(self)
        # This spacing will apply to all sub layouts
        self.main_layout.setSpacing(10)

        # Title Label for existing project selection
        self.existing_project_label = QLabel("Existing Projects")
        self.main_layout.addWidget(self.existing_project_label, alignment=Qt.AlignmentFlag.AlignCenter)

        # form layout for existing project selection
        self.existing_project_selection_layout = QFormLayout()
        self.existing_project_selection_layout.setFieldGrowthPolicy(QFormLayout.AllNonFixedFieldsGrow)
        self.existing_project_selection_layout.setSpacing(5)

        self.existing_project_label = QLabel("Existing Projects:")
        self.existing_project_combobox = QComboBox()

        self.existing_project_selection_layout.addRow(self.existing_project_label, self.existing_project_combobox)
        self.main_layout.addLayout(self.existing_project_selection_layout)

        # Select button for existing project
        self.select_existing_project_button = QPushButton("Select")
        self.select_existing_project_button.adjustSize()
        self.main_layout.addWidget(self.select_existing_project_button, alignment=Qt.AlignmentFlag.AlignRight)

        # Title Label for new project creation
        self.new_project_label = QLabel("New Project")
        self.main_layout.addWidget(self.new_project_label, alignment=Qt.AlignmentFlag.AlignCenter)

        # New Project Form
        self.new_project_layout = QFormLayout()
        self.new_project_layout.setFieldGrowthPolicy(QFormLayout.AllNonFixedFieldsGrow)
        self.new_project_layout.setSpacing(5)

        self.project_name_label = QLabel("Project Title*:")
        self.project_name_lineedit = QLineEdit()

        self.project_type_label = QLabel("Project Type*:")
        self.project_type_combobox = QComboBox()
        for project_type in PROJECT_TYPES.keys():
            self.project_type_combobox.addItem(project_type)

        self.project_url_label = QLabel("Project URL:")
        self.project_url_lineedit = QLineEdit()

        self.new_project_layout.addRow(self.project_name_label, self.project_name_lineedit)
        self.new_project_layout.addRow(self.project_type_label, self.project_type_combobox)
        self.new_project_layout.addRow(self.project_url_label, self.project_url_lineedit)

        self.main_layout.addLayout(self.new_project_layout)

        # Create button for new project
        self.create_new_project_button = QPushButton("Create")
        self.create_new_project_button.adjustSize()
        self.main_layout.addWidget(self.create_new_project_button, alignment=Qt.AlignmentFlag.AlignRight)

    def refresh_ui(self):
        """
        Refresh the input fields for the project widget.
        """
        self.existing_project_combobox.clear()
        self.project_name_lineedit.clear()
        self.project_url_lineedit.clear()

    def set_existing_projects(self, projects: list):
        """
        Set the items in the existing project combobox.

        :param projects: List of project titles to add to the combobox.
        """
        self.existing_project_combobox.clear()
        self.existing_project_combobox.addItems(projects)

    def get_existing_project_title(self) -> str:
        """
        Get the selected existing project title.

        :return: The title of the selected existing project.
        """
        return self.existing_project_combobox.currentText()

    def get_new_proj_info(self) -> tuple:
        """
        Get the new project information.

        :return: A tuple containing the project name, project type, and project URL.
        """
        return (self.project_name_lineedit.text(),
                self.project_type_combobox.currentText(),
                self.project_url_lineedit.text())

    @property
    def select_existing_project_signal(self):
        """
        Signal for the existing project selection button.

        :return: The clicked signal of the select existing project button.
        """
        return self.select_existing_project_button.clicked

    @property
    def create_new_project_signal(self):
        """
        Signal for the create new project button.

        :return: The clicked signal of the create new project button.
        """
        return self.create_new_project_button.clicked


class ScholarSelAugWidget(QWidget):
    """
    Widget for selecting and creating augmentations within a project.
    """

    def __init__(self):
        """
        Initialize the ScholarSelAugWidget.
        """
        super().__init__()
        self.setup_ui()

    def setup_ui(self):
        """
        Set up the UI for the augmentation selection widget.
        """
        self.main_layout = QVBoxLayout(self)
        # This spacing will apply to all sub layouts
        self.main_layout.setSpacing(10)

        # Title Label for project selection
        self.project_title_label = QLabel("Project: (Project Title)")
        self.main_layout.addWidget(self.project_title_label, alignment=Qt.AlignmentFlag.AlignCenter)

        # Title Label for augmentation selection
        self.create_new_augmentation_title_label = QLabel("Create New Augmentation")
        self.main_layout.addWidget(self.create_new_augmentation_title_label, alignment=Qt.AlignmentFlag.AlignCenter)

        # form for augmentation creation
        self.create_new_augmentation_layout = QFormLayout()
        self.create_new_augmentation_layout.setFieldGrowthPolicy(QFormLayout.AllNonFixedFieldsGrow)
        self.create_new_augmentation_layout.setSpacing(5)

        self.augmentation_name_label = QLabel("Augmentation Name*:")
        self.augmentation_title_lineedit = QLineEdit()

        self.create_new_augmentation_layout.addRow(self.augmentation_name_label, self.augmentation_title_lineedit)

        self.main_layout.addLayout(self.create_new_augmentation_layout)

        # Create button for new augmentation
        self.create_new_augmentation_button = QPushButton("Create New")
        self.create_new_augmentation_button.adjustSize()
        self.main_layout.addWidget(self.create_new_augmentation_button, alignment=Qt.AlignmentFlag.AlignRight)

        # Title Label for augmentation selection
        self.augmentation_label = QLabel("Select Existing Augmentation:")
        self.main_layout.addWidget(self.augmentation_label, alignment=Qt.AlignmentFlag.AlignCenter)

        # form for augmentation selection
        self.augmentation_selection_layout = QFormLayout()
        self.augmentation_selection_layout.setFieldGrowthPolicy(QFormLayout.AllNonFixedFieldsGrow)
        self.augmentation_selection_layout.setSpacing(5)

        self.existing_augs_label = QLabel("Augmentations:")
        self.augmentation_combobox = QComboBox()

        self.augmentation_selection_layout.addRow(self.existing_augs_label, self.augmentation_combobox)
        self.main_layout.addLayout(self.augmentation_selection_layout)

        # select existing augmentation button
        self.select_existing_augmentation_button = QPushButton("Select")
        self.select_existing_augmentation_button.adjustSize()
        self.main_layout.addWidget(self.select_existing_augmentation_button, alignment=Qt.AlignmentFlag.AlignRight)

    def refresh_ui(self):
        """
        Refresh the input fields for the augmentation selection widget.
        """
        self.augmentation_title_lineedit.clear()
        self.augmentation_combobox.clear()
        self.project_title_label.clear()

    def set_project_title(self, title):
        """
        Set the project title label.

        :param title: The title of the project.
        """
        self.project_title_label.setText(f"Project: {title}")

    def get_new_aug_title(self) -> str:
        """
        Get the new augmentation title.

        :return: The title of the new augmentation.
        """
        return self.augmentation_title_lineedit.text()

    def set_existing_augmentations(self, augmentations: list):
        """
        Set the items in the existing augmentations combobox.

        :param augmentations: List of augmentation titles to add to the combobox.
        """
        self.augmentation_combobox.clear()
        self.augmentation_combobox.addItems(augmentations)

    def get_existing_aug_selection(self) -> str:
        """
        Get the selected existing augmentation title.

        :return: The title of the selected existing augmentation.
        """
        return self.augmentation_combobox.currentText()

    @property
    def create_new_aug_signal(self):
        """
        Signal for the create new augmentation button.

        :return: The clicked signal of the create new augmentation button.
        """
        return self.create_new_augmentation_button.clicked

    @property
    def select_existing_aug_signal(self):
        """
        Signal for the select existing augmentation button.

        :return: The clicked signal of the select existing augmentation button.
        """
        return self.select_existing_augmentation_button.clicked


class ScholarAugEditWidget(QWidget):
    """
    Widget for editing augmentations within a project.
    """

    def __init__(self):
        """
        Initialize the ScholarAugEditWidget.
        """
        super().__init__()
        self.setup_ui()

    def setup_ui(self):
        """
        Set up the UI for the augmentation edit widget.
        """
        self.main_layout = QVBoxLayout(self)

        # Title label for the active project
        self.project_title_label = QLabel("Project: (Project Title)")
        self.main_layout.addWidget(self.project_title_label, alignment=Qt.AlignmentFlag.AlignCenter)

        # Title Label for active augmentation
        self.augmentation_title_label = QLabel("Selected Augmentation: (Augmentation Title)")
        self.main_layout.addWidget(self.augmentation_title_label, alignment=Qt.AlignmentFlag.AlignCenter)

        # Horizontal layout to split the augmentation preview and the action buttons
        self.preview_action_layout = QHBoxLayout()

        self.target_image_pixmap_label = QLabel()
        self.target_image_pixmap_label.setFixedSize(350, 200)
        self.target_image_pixmap_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.preview_action_layout.addWidget(self.target_image_pixmap_label)

        # Create all the buttons for the augmentation actions
        self.augmentation_action_layout = QVBoxLayout()

        self.update_target_image_button = QPushButton("Update Target Image")
        self.update_model_button = QPushButton("Update Model")
        self.preview_aug_button = QPushButton("Preview")
        self.save_files_locally_button = QPushButton("Save Files Locally")
        self.save_and_close_button = QPushButton("Save and Close")

        self.augmentation_action_layout.addWidget(self.update_target_image_button)
        self.augmentation_action_layout.addWidget(self.update_model_button)
        self.augmentation_action_layout.addWidget(self.preview_aug_button)
        self.augmentation_action_layout.addWidget(self.save_files_locally_button)
        self.augmentation_action_layout.addWidget(self.save_and_close_button)

        self.preview_action_layout.addLayout(self.augmentation_action_layout)

        self.preview_action_layout.setStretch(0, 4)
        self.preview_action_layout.setStretch(1, 1)

        self.main_layout.addLayout(self.preview_action_layout)

    def refresh_ui(self):
        """
        Refresh the input fields for the augmentation edit widget.
        """
        self.target_image_pixmap_label.clear()
        self.project_title_label.clear()
        self.augmentation_title_label.clear()

    def set_project_title(self, title):
        """
        Set the project title label.

        :param title: The title of the project.
        """
        self.project_title_label.setText(f"Project: {title}")

    def set_augmentation_title(self, title):
        """
        Set the augmentation title label.

        :param title: The title of the augmentation.
        """
        self.augmentation_title_label.setText(f"Selected Augmentation: {title}")

    def update_target_image_display(self, image_path):
        """
        Update the target image display.

        :param image_path: The path to the target image.
        """
        self.target_image_pixmap_label.clear()

        pixmap = QPixmap(image_path)
        # Find if the width or height is more restrictive and scale to that
        max_width = self.target_image_pixmap_label.maximumWidth()
        max_height = self.target_image_pixmap_label.maximumHeight()
        if pixmap.width() / max_width > pixmap.height() / max_height:
            scaled_pixmap = pixmap.scaledToWidth(max_width, Qt.TransformationMode.SmoothTransformation)
        else:
            scaled_pixmap = pixmap.scaledToHeight(max_height, Qt.TransformationMode.SmoothTransformation)

        self.target_image_pixmap_label.setPixmap(scaled_pixmap)
        return

    @property
    def update_target_image_signal(self):
        """
        Signal for the update target image button.

        :return: The clicked signal of the update target image button.
        """
        return self.update_target_image_button.clicked

    @property
    def update_model_signal(self):
        """
        Signal for the update model button.

        :return: The clicked signal of the update model button.
        """
        return self.update_model_button.clicked

    @property
    def preview_aug_signal(self):
        """
        Signal for the preview augmentation button.

        :return: The clicked signal of the preview augmentation button.
        """
        return self.preview_aug_button.clicked

    @property
    def save_files_locally_signal(self):
        """
        Signal for the save files locally button.

        :return: The clicked signal of the save files locally button.
        """
        return self.save_files_locally_button.clicked

    @property
    def save_and_close_signal(self):
        """
        Signal for the save and close button.

        :return: The clicked signal of the save and close button.
        """
        return self.save_and_close_button.clicked


class ScholarMainLayout(QVBoxLayout):
    """
    Main layout for the Scholar application, managing different widgets for login, project selection,
    augmentation selection, and augmentation editing.
    """

    LOGIN = 0
    PROJECT_SELECT = 1
    AUGMENTATION_SELECT = 2
    AUGMENTATION_EDIT = 3

    def __init__(self, parent=None):
        """
        Initialize the ScholarMainLayout.

        :param parent: The parent widget, if any.
        """
        super().__init__(parent)
        parent.setLayout(self)

        self.setSpacing(5)

        self.main_stack = QStackedLayout()
        self.addLayout(self.main_stack)

        self.main_stack.insertWidget(ScholarMainLayout.LOGIN, ScholarLoginWidget())
        self.main_stack.insertWidget(ScholarMainLayout.PROJECT_SELECT, ScholarProjectWidget())
        self.main_stack.insertWidget(ScholarMainLayout.AUGMENTATION_SELECT, ScholarSelAugWidget())
        self.main_stack.insertWidget(ScholarMainLayout.AUGMENTATION_EDIT, ScholarAugEditWidget())

        self.line = QFrame()
        self.line.setFrameShape(QFrame.Shape.HLine)
        self.line.setFrameShadow(QFrame.Shadow.Sunken)
        self.addWidget(self.line)

        self.lower_menu_layout = QHBoxLayout()

        self.max_nav_button_width = 150

        self.view_at_scholar_button = QPushButton("View at Schol-AR.io")
        self.view_at_scholar_button.adjustSize()
        self.view_at_scholar_button.setMaximumWidth(self.max_nav_button_width)
        self.view_at_scholar_button.clicked.connect(
            lambda: QDesktopServices().openUrl(QUrl("https://www.schol-ar.io/MyAugmentations")))

        self.login_button = QPushButton("New Login")
        self.login_button.adjustSize()
        self.login_button.setMaximumWidth(self.max_nav_button_width)

        self.project_button = QPushButton("Projects")
        self.project_button.adjustSize()
        self.project_button.setMaximumWidth(self.max_nav_button_width)

        self.augmentation_button = QPushButton("Augmentations")
        self.augmentation_button.adjustSize()
        self.augmentation_button.setMaximumWidth(self.max_nav_button_width)

        self.store_qr_button = QPushButton("Store QR")
        self.store_qr_button.adjustSize()
        self.store_qr_button.setMaximumWidth(self.max_nav_button_width)

        self.lower_menu_layout.addWidget(self.view_at_scholar_button)
        self.lower_menu_layout.addWidget(self.login_button)
        self.lower_menu_layout.addWidget(self.project_button)
        self.lower_menu_layout.addWidget(self.augmentation_button)
        self.lower_menu_layout.addWidget(self.store_qr_button)

        self.addLayout(self.lower_menu_layout)

    def set_active_widget(self, widget: int):
        """
        Set the active widget in the main stack. Use the class constants (LOGIN, PROJECT_SELECT, AUGMENTATION_SELECT,
        AUGMENTATION_EDIT) to set the widget.

        :param widget: The index of the widget to set as active.
        """
        self.main_stack.setCurrentIndex(widget)
        
        if widget == ScholarMainLayout.LOGIN:
            self.view_at_scholar_button.hide()
            self.login_button.hide()
            self.project_button.hide()
            self.augmentation_button.hide()
            self.store_qr_button.hide()
        elif widget == ScholarMainLayout.PROJECT_SELECT:
            self.view_at_scholar_button.show()
            self.login_button.show()
            self.project_button.hide()
            self.augmentation_button.hide()
            self.store_qr_button.hide()
        elif widget == ScholarMainLayout.AUGMENTATION_SELECT:
            self.view_at_scholar_button.show()
            self.login_button.show()
            self.project_button.show()
            self.augmentation_button.hide()
            self.store_qr_button.show()
        elif widget == ScholarMainLayout.AUGMENTATION_EDIT:
            self.view_at_scholar_button.show()
            self.login_button.show()
            self.project_button.show()
            self.augmentation_button.show()
            self.store_qr_button.show()

    def get_login_widget(self) -> ScholarLoginWidget:
        """
        Get the login widget.

        :return: The login widget.
        """
        return self.main_stack.widget(0)

    def get_project_widget(self) -> ScholarProjectWidget:
        """
        Get the project widget.

        :return: The project widget.
        """
        return self.main_stack.widget(1)

    def get_aug_sel_widget(self) -> ScholarSelAugWidget:
        """
        Get the augmentation selection widget.

        :return: The augmentation selection widget.
        """
        return self.main_stack.widget(2)

    def get_augmentation_edit_widget(self) -> ScholarAugEditWidget:
        """
        Get the augmentation edit widget.

        :return: The augmentation edit widget.
        """
        return self.main_stack.widget(3)

    @property
    def return_login_page_signal(self):
        """
        Signal for the return to login page button.

        :return: The clicked signal of the return to login page button.
        """
        return self.login_button.clicked

    @property
    def return_project_page_signal(self):
        """
        Signal for the return to project page button.

        :return: The clicked signal of the return to project page button.
        """
        return self.project_button.clicked

    @property
    def save_qr_signal(self):
        """
        Signal for the save QR button.

        :return: The clicked signal of the save QR button.
        """
        return self.store_qr_button.clicked

    @property
    def return_augmentation_page_signal(self):
        """
        Signal for the return to augmentation page button.

        :return: The clicked signal of the return to augmentation page button.
        """
        return self.augmentation_button.clicked
