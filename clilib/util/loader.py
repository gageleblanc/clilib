from pathlib import Path
import json
from sys import platform


class Loader:
    @staticmethod
    def getActiveModules():
        if platform == "win32":
            with open("C:\\Python38\\upldr_config\\modules.json") as f:
                moduleSpec = json.load(f)
            return moduleSpec
        else:
            user_home = str(Path.home())
            with open(user_home + "/.local/upldr_config/modules.json") as f:
                moduleSpec = json.load(f)
            return moduleSpec
