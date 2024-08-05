from Qt.QtCore import Qt
from Qt.QtGui import QPixmap
from Qt.QtWidgets import (QFrame, QVBoxLayout, QWidget, QComboBox, QFormLayout, QLabel, QLineEdit,
                          QPushButton, QHBoxLayout, QStackedLayout)

from .io import APIManager


class ScholarAugPreviewWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.setup_aug_preview_ui()

    def setup_aug_preview_ui(self):
        self.layout = QVBoxLayout(self)

        # Create a horizontal layout to the preview label and the label stack for the qr and tracking score
        self.h_layout = QHBoxLayout()

        # Main preview label
        self.previewLabel = QLabel()
        self.h_layout.addWidget(self.previewLabel)

        # Track-score label and QR code label with vertical layout to align it to the bottom
        self.qrLabelLayout = QVBoxLayout()

        # tracking score label
        self.tracking_score_label = QLabel("Tracking Score: 0/5")

        # Support links in the tracking score label.
        self.tracking_score_label.setOpenExternalLinks(True)
        self.tracking_score_label.setTextFormat(Qt.TextFormat.RichText)

        self.qrLabelLayout.addWidget(self.tracking_score_label)

        # QR code labels for pixmap
        self.pub_qr_label = QLabel()
        self.pub_qr_label.setFixedSize(150, 150)
        self.qrLabelLayout.addWidget(self.pub_qr_label)
        self.admin_qr_label = QLabel()
        self.admin_qr_label.setFixedSize(150, 150)
        self.qrLabelLayout.addWidget(self.admin_qr_label)

        # Add the vertical layout containing the QR label to the horizontal layout
        self.h_layout.addLayout(self.qrLabelLayout)

        # Add the horizontal layout to the main layout
        self.layout.addLayout(self.h_layout)

        # Set the alignment of the main layout to top left
        self.layout.setAlignment(Qt.AlignTop | Qt.AlignLeft)

        self.setLayout(self.layout)

    @staticmethod
    def create_new_aug_preview_ui(child_window, target_image_path, pub_qr_path, admin_qr_path, tracking_score):
        preview_widget = ScholarAugPreviewWidget()
        preview_widget.assign_to_preview_window(child_window)
        preview_widget.preview_aug(target_image_path, pub_qr_path, admin_qr_path, tracking_score)

    def preview_aug(self, preview_image_path, pub_qr_path, admin_qr_path, tracking_score):
        preview_pixmap = QPixmap(preview_image_path)
        self.previewLabel.setPixmap(
            preview_pixmap.scaled(self.previewLabel.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation)
        )

        if tracking_score < 0:
            self.tracking_score_label.setText(f"Try refreshing in a moment for Tracking Score.")
        elif tracking_score < 30:
            self.tracking_score_label.setText(f"Tracking Score: {int(tracking_score//20)}/5 <br> Image tracking may be acceptable "
                                              f"but could be improved.<br> <a href=\"https://www.schol-ar.io/AugImages"
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
        This needs to be called before preview_aug is called so that the layout is set and the window size can pick up
        on the right sizeHints
        """
        tool_window.setLayout(self.layout)


class ScholarLoginWidget(QWidget):

    def __init__(self):
        super().__init__()
        self.setup_ui()

    def setup_ui(self):
        self.main_layout = QVBoxLayout(self)
        # This spacing will apply to all sub layouts
        self.main_layout.setSpacing(10)

        # Label for existing user selection
        self.existing_user_label = QLabel("Existing User")
        self.main_layout.addWidget(self.existing_user_label, alignment=Qt.AlignmentFlag.AlignCenter)

        # form layout for existing user selection
        self.existing_user_selection_layout = QFormLayout()
        self.existing_user_selection_layout.setFieldGrowthPolicy(QFormLayout.AllNonFixedFieldsGrow)
        self.existing_user_selection_layout.setSpacing(5)

        self.existing_user_label = QLabel("Existing User:")
        self.existing_user_combobox = QComboBox()

        self.existing_user_selection_layout.addRow(self.existing_user_label, self.existing_user_combobox)

        self.main_layout.addLayout(self.existing_user_selection_layout)

        # Submit button for existing user
        self.select_existing_user_button = QPushButton("Select Existing User")
        self.select_existing_user_button.adjustSize()
        self.main_layout.addWidget(self.select_existing_user_button, alignment=Qt.AlignmentFlag.AlignRight)

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

        # Submit button for new user
        self.submit_new_user_button = QPushButton("Submit")
        self.submit_new_user_button.adjustSize()
        self.main_layout.addWidget(self.submit_new_user_button, alignment=Qt.AlignmentFlag.AlignRight)

    def refresh_iu(self):
        self.existing_user_combobox.clear()
        self.user_lineedit.clear()
        self.api_token_lineedit.clear()

    def set_login_combobox(self, users: list):
        self.existing_user_combobox.clear()
        self.existing_user_combobox.addItems(users)

    def get_exiting_user(self) -> str:
        return self.existing_user_combobox.currentText()

    def get_new_login_info(self) -> tuple:
        """
        :return: (username, api_token)
        """
        return self.user_lineedit.text(), self.api_token_lineedit.text()

    @property
    def new_user_signal(self):
        return self.submit_new_user_button.clicked

    @property
    def existing_user_signal(self):
        return self.select_existing_user_button.clicked


class ScholarProjectWidget(QWidget):

    def __init__(self):
        super().__init__()
        self.setup_ui()

    def setup_ui(self):
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
        for project_type in APIManager.PROJECT_TYPES.keys():
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
        self.existing_project_combobox.clear()
        self.project_name_lineedit.clear()
        self.project_url_lineedit.clear()

    def set_existing_projects(self, projects: list):
        self.existing_project_combobox.clear()
        self.existing_project_combobox.addItems(projects)

    def get_existing_project_title(self) -> str:
        return self.existing_project_combobox.currentText()

    def get_new_proj_info(self) -> tuple:
        """
        :return: (project_name, project_type, project_url)
        """
        return (self.project_name_lineedit.text(),
                self.project_type_combobox.currentText(),
                self.project_url_lineedit.text())

    @property
    def select_existing_project_signal(self):
        return self.select_existing_project_button.clicked

    @property
    def create_new_project_signal(self):
        return self.create_new_project_button.clicked


class ScholarSelAugWidget(QWidget):

    def __init__(self):
        super().__init__()
        self.setup_ui()

    def setup_ui(self):
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
        self.augmentation_title_lineedit.clear()
        self.augmentation_combobox.clear()
        self.project_title_label.clear()

    def set_project_title(self, title):
        self.project_title_label.setText(f"Project: {title}")

    def get_new_aug_title(self) -> str:
        return self.augmentation_title_lineedit.text()

    def set_existing_augmentations(self, augmentations: list):
        self.augmentation_combobox.clear()
        self.augmentation_combobox.addItems(augmentations)

    def get_existing_aug_selection(self) -> str:
        return self.augmentation_combobox.currentText()

    @property
    def create_new_aug_signal(self):
        return self.create_new_augmentation_button.clicked

    @property
    def select_existing_aug_signal(self):
        return self.select_existing_augmentation_button.clicked


class ScholarAugEditWidget(QWidget):

    def __init__(self):
        super().__init__()
        self.setup_ui()

    def setup_ui(self):
        self.main_layout = QVBoxLayout(self)

        # Title label for the active project
        self.project_title_label = QLabel("Project: (Project Title)")
        self.main_layout.addWidget(self.project_title_label, alignment=Qt.AlignmentFlag.AlignCenter)

        # Title Label for active augmentation
        self.augmentation_title_label = QLabel("Selected Augmentation: (Augmentation Title)")
        self.main_layout.addWidget(self.augmentation_title_label, alignment=Qt.AlignmentFlag.AlignCenter)

        # Horizontal layout to split the augmentation preview and the action buttons
        self.preview_action_layout = QHBoxLayout()

        # Create a vertical layout for the augmentation preview
        self.preview_layout = QVBoxLayout()

        self.target_image_pixmap_label = QLabel()
        self.target_image_pixmap_label.setMaximumWidth(400)
        self.preview_layout.addWidget(self.target_image_pixmap_label)

        self.preview_action_layout.addLayout(self.preview_layout)

        # Create all the buttons for the augmentation actions
        self.augmentation_action_layout = QVBoxLayout()

        self.update_target_image_button = QPushButton("Update Target Image")
        self.update_model_button = QPushButton("Update Model")
        self.preview_aug_button = QPushButton("Preview")
        self.store_target_image_button = QPushButton("Store Target Image")
        self.save_and_close_button = QPushButton("Save and Close")

        self.augmentation_action_layout.addWidget(self.update_target_image_button)
        self.augmentation_action_layout.addWidget(self.update_model_button)
        self.augmentation_action_layout.addWidget(self.preview_aug_button)
        self.augmentation_action_layout.addWidget(self.store_target_image_button)
        self.augmentation_action_layout.addWidget(self.save_and_close_button)

        self.preview_action_layout.addLayout(self.augmentation_action_layout)

        self.preview_action_layout.setStretch(0, 4)
        self.preview_action_layout.setStretch(1, 1)

        self.main_layout.addLayout(self.preview_action_layout)

    def refresh_ui(self):
        self.target_image_pixmap_label.clear()
        self.project_title_label.clear()
        self.augmentation_title_label.clear()

    def set_project_title(self, title):
        self.project_title_label.setText(f"Project: {title}")

    def set_augmentation_title(self, title):
        self.augmentation_title_label.setText(f"Selected Augmentation: {title}")

    def set_preview_image(self, image_path):
        self.target_image_pixmap_label.clear()
        pixmap = QPixmap(image_path)
        self.target_image_pixmap_label.setPixmap(pixmap)

    def update_target_image_display(self, image_path):
        self.target_image_pixmap_label.clear()
        pixmap = QPixmap(image_path).scaledToWidth(
            self.target_image_pixmap_label.maximumWidth(), Qt.TransformationMode.SmoothTransformation)
        self.target_image_pixmap_label.setPixmap(pixmap)

    @property
    def update_target_image_signal(self):
        return self.update_target_image_button.clicked

    @property
    def update_model_signal(self):
        return self.update_model_button.clicked

    @property
    def preview_aug_signal(self):
        return self.preview_aug_button.clicked

    @property
    def store_target_image_signal(self):
        return self.store_target_image_button.clicked

    @property
    def save_and_close_signal(self):
        return self.save_and_close_button.clicked


class ScholarMainLayout(QVBoxLayout):

    LOGIN = 0
    PROJECT_SELECT = 1
    AUGMENTATION_SELECT = 2
    AUGMENTATION_EDIT = 3

    def __init__(self, parent=None):
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

        self.login_button = QPushButton("Login")
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

        self.lower_menu_layout.addWidget(self.login_button)
        self.lower_menu_layout.addWidget(self.project_button)
        self.lower_menu_layout.addWidget(self.augmentation_button)
        self.lower_menu_layout.addWidget(self.store_qr_button)

        self.addLayout(self.lower_menu_layout)

    def set_active_widget(self, widget: int):
        """
        :param widget: use class variables to set the widget
        """
        self.main_stack.setCurrentIndex(widget)
        
        if widget == ScholarMainLayout.LOGIN:
            self.login_button.hide()
            self.project_button.hide()
            self.augmentation_button.hide()
            self.store_qr_button.hide()
        elif widget == ScholarMainLayout.PROJECT_SELECT:
            self.login_button.show()
            self.project_button.hide()
            self.augmentation_button.hide()
            self.store_qr_button.hide()
        elif widget == ScholarMainLayout.AUGMENTATION_SELECT:
            self.login_button.show()
            self.project_button.show()
            self.augmentation_button.hide()
            self.store_qr_button.show()
        elif widget == ScholarMainLayout.AUGMENTATION_EDIT:
            self.login_button.show()
            self.project_button.show()
            self.augmentation_button.show()
            self.store_qr_button.show()

    def get_login_widget(self) -> ScholarLoginWidget:
        return self.main_stack.widget(0)

    def get_project_widget(self) -> ScholarProjectWidget:
        return self.main_stack.widget(1)

    def get_aug_sel_widget(self) -> ScholarSelAugWidget:
        return self.main_stack.widget(2)

    def get_augmentation_edit_widget(self) -> ScholarAugEditWidget:
        return self.main_stack.widget(3)

    @property
    def return_login_page_signal(self):
        return self.login_button.clicked

    @property
    def return_project_page_signal(self):
        return self.project_button.clicked

    @property
    def save_qr_signal(self):
        return self.store_qr_button.clicked

    @property
    def return_augmentation_page_signal(self):
        return self.augmentation_button.clicked
