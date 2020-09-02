from pathlib import Path
import json
from sys import platform


class Loader:
    @staticmethod
    def getActiveModules(path):
        if platform == "win32":
            with open(path) as f:
                moduleSpec = json.load(f)
            return moduleSpec
        else:
            with open(path) as f:
                moduleSpec = json.load(f)
            return moduleSpec
