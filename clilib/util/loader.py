from pathlib import Path
import json
from sys import platform

from clilib.util.arg_tools import arg_tools
import importlib


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

    @staticmethod
    def start_app(modules, modules_base):
        args, _ = arg_tools.command_parser(modules)
        try:
            module = importlib.import_module(modules_base + "." + args.command[0] + ".main")
            module.main()
        except ImportError as ex:
            print("Command not found: " + args.command[0] + ". Command must be one of " + ", ".join(modules))
            print(ex)
        except SystemExit as _:
            exit(0)
        except KeyboardInterrupt as kbi:
            print("User keyboard interrupt!")
            exit(1)
