from chimerax.core.toolshed import BundleAPI
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


# Create the ``bundle_api`` object that ChimeraX expects.
bundle_api = _MyAPI()
