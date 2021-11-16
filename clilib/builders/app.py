import importlib

import argparse

from clilib.util.logging import Logging
from clilib.util.arg_tools import arg_tools


class CLIApp:
    def __init__(self, prefix_path: str = None, app_name: str = "CLIApp"):
        self.prefix_path = prefix_path
        self.prefix = False
        if prefix_path is not None:
            self.prefix = True
        self.logger = Logging(app_name).get_logger()
        self.subcommands = {}

    def add_subcommand(self, name: str, path: str):
        """
        Add subcommand to this CLI app
        :param name: subcommand name to use
        :param path: path to python module
        :return: void
        """
        self.subcommands[name] = path

    def command_parser(self):
        parser = argparse.ArgumentParser(add_help=False)
        parser.add_argument("-h", "--help", action="help", help="show this help message and exit")
        parser.add_argument('command', choices=self.subcommands.keys(), nargs=argparse.REMAINDER)
        args, _ = parser.parse_known_args()
        if len(args.command) > 0:
            return args
        else:
            parser.print_help()
            exit(1)

    def execute_command(self, args):
        if args.command[0] in self.subcommands:
            path = self.subcommands[args.command[0]]
            if self.prefix:
                path = "%s.%s" % (self.prefix_path, path)
            try:
                # path_parts = path.split(".")
                module = importlib.import_module(path)
                if hasattr(module, "main"):
                    module.main()
                else:
                    self.logger.fatal("Subcommand %s is missing `main()` function, cannot run." % args.command[0])
                    exit(1)
            except ImportError as ex:
                self.logger.fatal("ImportError encountered in subcommand: %s. This is usually caused by an error in the module or app configuration." % args.command[0])
                print(ex)
                return False
            except SystemExit as sys_exit:
                exit(sys_exit.code)
            except KeyboardInterrupt:
                self.logger.warn("User keyboard interrupt!")
                exit(1)
        else:
            self.logger.fatal("Command not found: %s. Command must be one of %s" % (args.command[0], ", ".join(self.subcommands.keys())))
            return False

    def start_app(self):
        # args, _ = arg_tools.command_parser(self.subcommands.keys())
        args = self.command_parser()
        self.logger.debug(args)
        self.execute_command(args)