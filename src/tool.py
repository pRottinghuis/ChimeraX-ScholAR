from typing import Optional

from Qt.QtGui import QAction
from chimerax.core.commands import run
from chimerax.core.tools import ToolInstance
from chimerax.ui import MainToolWindow
from chimerax.ui.open_save import SaveDialog

from .io import ScARFileManager, APIManager
from .scholar_ui import ScholarMainLayout, ScholarLoginWidget, ScholarProjectWidget, ScholarSelAugWidget, \
    ScholarAugEditWidget, ScholarAugPreviewWidget


class ChimeraXScholARTool(ToolInstance):
    SESSION_ENDURING = True  # Does this instance persist when session closes
    SESSION_SAVE = False  # We do not save/restore in sessions
    help = "help:user/tools/chimerax-scholar.html"

    def __init__(self, session, tool_name):
        super().__init__(session, tool_name)

        # These fields must be set whenever the tool logs in a new user, selects a project, or selects an augmentation.
        self.active_user = None
        self.active_project = None
        self.active_augmentation = None

        # Create the main window for our tool.
        # The window isn't shown until we call its 'manage' method.
        self.tool_window = MainToolWindow(self)
        self.main_layout: ScholarMainLayout = ScholarMainLayout(self.tool_window.ui_area)

        self.setup_ui()
        self.tool_window.fill_context_menu = self.fill_context_menu

        self.tool_window.manage("side")

    def setup_ui(self):
        self.select_login_page()

        # Login widget signals
        login_widget: ScholarLoginWidget = self.main_layout.get_login_widget()
        login_widget.new_user_signal.connect(lambda: self.submit_new_user())
        login_widget.existing_user_signal.connect(lambda: self.submit_existing_user())

        # Project selection signals
        project_widget: ScholarProjectWidget = self.main_layout.get_project_widget()
        project_widget.select_existing_project_signal.connect(lambda: self.select_existing_project())
        project_widget.create_new_project_signal.connect(lambda: self.select_new_project())

        # Augmentation signals
        aug_sel_widget: ScholarSelAugWidget = self.main_layout.get_aug_sel_widget()
        aug_sel_widget.select_existing_aug_signal.connect(lambda: self.select_existing_augmentation())
        aug_sel_widget.create_new_aug_signal.connect(lambda: self.select_new_augmentation())

        # Augmentation edit signals
        aug_edit_widget = self.main_layout.get_augmentation_edit_widget()
        aug_edit_widget.update_target_image_signal.connect(lambda: self.update_target_image())
        aug_edit_widget.update_model_signal.connect(
            lambda: self.update_aug_files(target_image=False, augmented_file=True))
        aug_edit_widget.preview_aug_signal.connect(lambda: self.preview_augmentation())
        aug_edit_widget.save_and_close_signal.connect(lambda: self.augmentation_back_page())
        aug_edit_widget.save_files_locally_signal.connect(lambda: self.store_files_locally())

        # Main layout navigation signals
        self.main_layout.return_login_page_signal.connect(lambda: self.login_back_page())
        self.main_layout.return_project_page_signal.connect(lambda: self.project_back_page())
        self.main_layout.save_qr_signal.connect(lambda: self.store_qr_image())
        self.main_layout.return_augmentation_page_signal.connect(lambda: self.augmentation_back_page())

    def select_login_page(self):
        # set up the use selection dropdown
        users_info = ScARFileManager.get_users_info()
        existing_users = []
        if users_info is not None:
            for user in users_info.keys():
                existing_users.append(user)

        self.main_layout.get_login_widget().refresh_iu()
        self.main_layout.get_login_widget().set_login_combobox(existing_users)

        # set the page to login
        self.main_layout.set_active_widget(ScholarMainLayout.LOGIN)

        # These resets are here for when the user has logged in and then goes back to the login page.
        self.active_user = None
        self.active_project = None
        self.active_augmentation = None

    def select_project_page(self):
        self.main_layout.get_project_widget().refresh_ui()

        project_titles = ScARFileManager.list_projects(self.active_user)
        self.main_layout.get_project_widget().set_existing_projects(project_titles)
        self.main_layout.set_active_widget(ScholarMainLayout.PROJECT_SELECT)

        self.active_project = None
        self.active_augmentation = None

    def select_augmentation_page(self):
        self.main_layout.get_aug_sel_widget().refresh_ui()
        augmentation_titles = ScARFileManager.list_existing_aug_titles(self.active_user, self.active_project)
        self.main_layout.get_aug_sel_widget().set_existing_augmentations(augmentation_titles)
        self.main_layout.set_active_widget(ScholarMainLayout.AUGMENTATION_SELECT)

    def select_aug_edit_page(self):
        aug_edit_widget: ScholarAugEditWidget = self.main_layout.get_augmentation_edit_widget()
        aug_edit_widget.refresh_ui()
        aug_edit_widget.set_project_title(self.active_project)
        aug_edit_widget.set_augmentation_title(self.active_augmentation)

        # Check if the target image exists locally. If not download it. Then set it to the widget for display.
        image_file_path = ScARFileManager.get_augmentation_target_image_path(
            self.active_user, self.active_project, self.active_augmentation)
        if image_file_path is None:
            run(self.session, f"scholar downloadAugFiles \"{self.active_user}\" \"{self.active_project}\" \"{self.active_augmentation}\" targetImage True augmentedFile False")
            image_file_path = ScARFileManager.get_augmentation_target_image_path(
                self.active_user, self.active_project, self.active_augmentation)

        self.main_layout.get_augmentation_edit_widget().update_target_image_display(image_file_path)

        self.main_layout.set_active_widget(ScholarMainLayout.AUGMENTATION_EDIT)

        run(self.session,
            f"scholar openAugSession \"{self.active_user}\" \"{self.active_project}\" \"{self.active_augmentation}\"")

    def login_back_page(self):
        """
        Goes back to the login page. Saves project currently being worked on.
        """
        self.close_aug()
        self.close_project()
        self.select_login_page()

    def project_back_page(self):
        """
        Goes back to the project page. Make sure to save project and aug if any currently being worked on.
        """
        self.close_aug()
        self.close_project()
        self.select_project_page()

    def augmentation_back_page(self):
        """
        Goes back to the project selection page from the augmentation selection page. Make sure to save augmentation
        currently being worked on.
        """
        self.close_aug()
        self.select_augmentation_page()

    def submit_new_user(self):
        username, api_token = self.main_layout.get_login_widget().get_new_login_info()

        # check if the fields are empty
        if username == "" or api_token == "":
            return

        # run the login command
        run(self.session, f"scholar login \"{username}\" \"{api_token}\"")
        # check if the login was successful and swap pages
        self.try_leave_login_page(username)

    def submit_existing_user(self):
        username = self.main_layout.get_login_widget().get_exiting_user()

        # case where there is nothing in the selection box. Should do nothing.
        if username == "":
            return

        run(self.session, f"scholar login \"{username}\"")
        # check if the login was successful and swap pages
        self.try_leave_login_page(username)

    def try_leave_login_page(self, username):
        if ScARFileManager().get_user_token(username) is not None:
            self.active_user = username
            self.select_project_page()

    def select_existing_project(self):
        project_title = self.main_layout.get_project_widget().get_existing_project_title()

        # case where there is nothing in the selection box. Should do nothing.
        if project_title == "":
            return

        run(self.session, f"scholar project \"{self.active_user}\" \"{project_title}\"")
        self.active_project = project_title
        self.select_augmentation_page()

    def select_new_project(self):
        project_title, unformatted_project_type, project_url = self.main_layout.get_project_widget().get_new_proj_info()

        # Project title must be listed
        if project_title == "":
            return

        project_type = APIManager.PROJECT_TYPES[unformatted_project_type]

        run(self.session,
            f"scholar project \"{self.active_user}\" \"{project_title}\" projectType \"{project_type}\" discUrl \"{project_url}\"")

        if ScARFileManager.get_project(self.active_user, project_title) is not None:
            self.active_project = project_title
            self.select_augmentation_page()

    def close_project(self):
        """
        Properly saves and closes a project. Add any additional steps here.
        """
        self.active_project = None

    def select_existing_augmentation(self):
        augmentation_title = self.main_layout.get_aug_sel_widget().get_existing_aug_selection()

        # case where there is nothing in the selection box. Should do nothing.
        if augmentation_title == "":
            return

        run(self.session,
            f"scholar augmentation \"{self.active_user}\" \"{self.active_project}\" \"{augmentation_title}\"")

        # Check if somehow the augmentation was not created or set
        if ScARFileManager.get_augmentation(self.active_user, self.active_project, augmentation_title) is None:
            return

        # save the active augmentation and open the session if it exists
        self.active_augmentation = augmentation_title

        self.select_aug_edit_page()

    def select_new_augmentation(self):
        new_title = self.main_layout.get_aug_sel_widget().get_new_aug_title()
        # New augmentation must have a title
        if new_title == "":
            return

        run(self.session,
            f"scholar augmentation \"{self.active_user}\" \"{self.active_project}\" \"{new_title}\"")

        # Check if somehow the augmentation was not created or set
        if ScARFileManager.get_augmentation(self.active_user, self.active_project, new_title) is None:
            return
        self.active_augmentation = new_title
        self.select_aug_edit_page()

    def close_aug(self):
        """
        Properly saves and closes an augmentation session.
        """
        if self.active_augmentation is None:
            return

        run(self.session,
            f"scholar saveAugSession \"{self.active_user}\" \"{self.active_project}\" \"{self.active_augmentation}\"")
        run(self.session, "close session")
        self.active_augmentation = None

    def update_aug_files(self, target_image: bool, augmented_file: bool):
        user = self.active_user
        project = self.active_project
        augmentation = self.active_augmentation

        # check if the user, project, and augmentation are all set
        if user is not None and project is not None and augmentation is not None:
            run(self.session,
                f"scholar uploadAugFiles \"{user}\" \"{project}\" \"{augmentation}\" targetImage {target_image} augmentedFile {augmented_file}")

    def update_target_image(self):
        self.update_aug_files(target_image=True, augmented_file=False)

        image_path = ScARFileManager.get_augmentation_target_image_path(
            self.active_user, self.active_project, self.active_augmentation)
        self.main_layout.get_augmentation_edit_widget().update_target_image_display(image_path)

    def preview_augmentation(self):
        # Can't preview if no user, project, or augmentation is selected
        if self.active_user is None or self.active_project is None or self.active_augmentation is None:
            return

        # Get the file path to the preview image
        target_image_path = ScARFileManager.get_augmentation_target_image_path(
            self.active_user, self.active_project, self.active_augmentation
        )

        # if there is no file path then there is nothing to preview
        if target_image_path is None:
            return

        # Get the qr image path. If it doesn't exist try downloading it.
        pub_qr_image_path = ScARFileManager.get_qr_file(self.active_user, self.active_project, admin=False)
        admin_qr_image_path = ScARFileManager.get_qr_file(self.active_user, self.active_project, admin=True)
        if pub_qr_image_path is None:
            run(self.session, f"scholar downloadQR \"{self.active_user}\" \"{self.active_project}\"")
            pub_qr_image_path = ScARFileManager.get_qr_file(self.active_user, self.active_project, admin=False)
            admin_qr_image_path = ScARFileManager.get_qr_file(self.active_user, self.active_project, admin=True)

        # Check if the qr image path is still none after trying to download. If it is then there is no qr code to
        # preview.
        if pub_qr_image_path is None:
            print("Can't preview because there is no QR code available.")
            return

        ScARFileManager.update_augs_info(self.active_user, self.active_project)

        tracking_score = ScARFileManager.get_aug_tracking_score(
            self.active_user, self.active_project, self.active_augmentation)

        # Child window made from main tool window
        preview_window = self.tool_window.create_child_window(f"{self.active_augmentation} Preview")
        ScholarAugPreviewWidget.create_new_aug_preview_ui(
            preview_window.ui_area, target_image_path, pub_qr_image_path, admin_qr_image_path, tracking_score)
        preview_window.manage(None)

    def store_files_locally(self):
        if self.active_user is None or self.active_project is None or self.active_augmentation is None:
            return

        file_path = self.save_in_folder()
        if file_path is None:
            return

        run(self.session, f"scholar storeAllAugFiles \"{self.active_user}\" \"{self.active_project}\" "
                          f"\"{self.active_augmentation}\" \"{file_path}\"")

    def store_qr_image(self):
        if self.active_user is None or self.active_project is None:
            return
        # Use dialog to get the file path to save the qr image to
        qr_im_fp = self.save_in_png_file()
        if qr_im_fp is None:
            return
        run(self.session, f"scholar storeQRImage \"{self.active_user}\" \"{self.active_project}\" \"{qr_im_fp}\"")

    def fill_context_menu(self, menu, x, y):
        clean_local_action = QAction("Clean Project Files", menu)
        clean_local_action.triggered.connect(lambda *args: self.clean_local())
        menu.addAction(clean_local_action)

    def save_in_png_file(self) -> Optional[str]:
        """
        Opens a save dialog for the user to select an image file to save to
        :return: str filename path for save or None if nothing was selected or something went wrong.
        """
        save_dialog = SaveDialog(self.session, parent=self.tool_window.ui_area)
        save_dialog.setNameFilter("PNG (*.png)")
        if save_dialog.exec():
            file_path = save_dialog.selectedFiles()[0]
            return file_path
        return None

    def save_in_folder(self) -> Optional[str]:
        """
        Opens a save dialog for the user to select a folder to save the files in.
        :return: str dir path or None if nothing was selected or something went wrong.
        """
        save_dialog = SaveDialog(self.session, parent=self.tool_window.ui_area)
        save_dialog.setFileMode(SaveDialog.Directory)
        save_dialog.setOption(SaveDialog.ShowDirsOnly, True)
        if save_dialog.exec():
            folder_path = save_dialog.selectedFiles()[0]
            return folder_path
        return None

    def clean_local(self):
        if self.active_user is not None:
            user_for_clear = self.active_user
            self.close_aug()
            self.close_project()
            self.select_login_page()
            run(self.session, f"scholar cleanLocal \"{user_for_clear}\"")

    def delete(self):
        # Safely close the augmentation with a session save before deleting the tool.
        self.close_aug()
        self.close_project()
        super().delete()
