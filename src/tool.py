from chimerax.core.tools import ToolInstance


class ChimeraXScholARTool(ToolInstance):

    # Inheriting from ToolInstance makes us known to the ChimeraX tool mangager,
    # so we can be notified and take appropriate action when sessions are closed,
    # saved, or restored, and we will be listed among running tools and so on.
    #
    # If cleaning up is needed on finish, override the 'delete' method
    # but be sure to call 'delete' from the superclass at the end.

    SESSION_ENDURING = False    # Does this instance persist when session closes
    SESSION_SAVE = True         # We do save/restore in sessions
    help = "help:user/tools/chimerax-scholar.html"
                                # Let ChimeraX know about our help page

    def __init__(self, session, tool_name):
        # 'session'   - chimerax.core.session.Session instance
        # 'tool_name' - string

        super().__init__(session, tool_name)

        # Create the main window for our tool.
        # The window isn't shown until we call its 'manage' method.
        from chimerax.ui import MainToolWindow
        self.tool_window = MainToolWindow(self)

        self._build_ui()

    def _build_ui(self):
        self.tool_window.manage('side')
