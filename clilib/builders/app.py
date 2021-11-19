import importlib
import argparse
import inspect
import re
import types

from clilib.builders.spec import SpecBuilder
from clilib.util.logging import Logging
from clilib.util.arg_tools import arg_tools

DEFAULT_FLAG_SPEC = {
    "names": [],
    "help": "Default flag help, use docstring to configure",
    "type": str,
    "default": None,
    "required": False
}

DEFAULT_POSITIONAL_SPEC = {
    "name": "default",
    "help": "Default flag help, use docstring to configure",
    "type": str
}

class EasyCLI:
    args: argparse.Namespace
    def __init__(self, obj, execute: bool = True):
        self._obj = obj
        if not isinstance(obj, types.FunctionType) and not inspect.isclass(obj):
            raise TypeError("EasyCLI requires class or method type, not %s" % str(type(obj)))
        self.name = obj.__name__.lower()
        self.desc = obj.__doc__.strip()
        self.anno = {}
        if isinstance(obj, types.FunctionType):
            self.anno = obj.__annotations__
        elif inspect.isclass(obj):
            self.anno = obj.__init__.__annotations__
        self.flag_spec = []
        self.positional_spec = []
        self._shortnames = []
        self.subcommand_spec = []
        self._sub_map = {}
        self.spec: SpecBuilder = SpecBuilder(self.name, self.desc.split("\n")[0])
        self._get_arguments()
        self._setup_argparse()
        if execute:
            self.execute_cli()

    def execute_cli(self):
        if isinstance(self._obj, types.FunctionType):
            self.args = arg_tools.build_simple_parser(self.spec.build())
            self._obj(**vars(self.args))
        elif inspect.isclass(self._obj):
            self.args = arg_tools.build_full_cli(self.spec.build())
            if self.args.subcommand not in self._sub_map:
                arg_tools.parser.print_help()
                exit(1)
            self._resolve_subcommand(self._obj, "subcommand")
            # arg_spec = inspect.getfullargspec(self._obj.__init__)
            # arg_spec.args.remove("self")
            # arg_dict = {}
            # for arg in arg_spec.args:
            #     arg_dict[arg] = getattr(self.args, arg)
            # o = self._obj(**arg_dict)
            # m = getattr(o, self._sub_map[self.args.subcommand])
            # sbcv = getattr(self.args, self.args.subcommand)
            # print(sbcv)
            # arg_spec = inspect.getfullargspec(m)
            # arg_spec.args.remove("self")
            # arg_dict = {}
            # for arg in arg_spec.args:
            #     arg_dict[arg] = getattr(self.args, arg)
            # m(**arg_dict)

    def _resolve_subcommand(self, obj, sub: str):
        if inspect.isclass(obj):
            arg_spec = inspect.getfullargspec(obj.__init__)
        elif inspect.ismethod(obj):
            arg_spec = inspect.getfullargspec(obj.__init__)
        elif isinstance(obj, types.FunctionType):
            arg_spec = inspect.getfullargspec(obj)
        else:
            raise TypeError("Unable to resolve subcommand path")
        arg_spec.args.remove("self")
        arg_dict = {}
        for arg in arg_spec.args:
            arg_dict[arg] = getattr(self.args, arg)
        o = obj(**arg_dict)
        if sub in self.args:
            s = getattr(self.args, sub)
            if s:
                f = s
                if s in self._sub_map:
                    f = self._sub_map[s]
                m = getattr(o, f)
                self._resolve_subcommand(m, s)
                return None
        if obj.__name__ != sub:
            arg_tools.parser.print_help()
            exit(1)

    def _setup_argparse(self):
        for flag in self.flag_spec:
            names = flag["names"]
            del flag["names"]
            self.spec.add_flag(*names, **flag)
        for positional in self.positional_spec:
            name = positional["name"]
            del positional["name"]
            self.spec.add_positional(name, **positional)
        for sub in self.subcommand_spec:
            self.spec.add_subcommand(sub)

    def _get_arguments(self):
        if inspect.isclass(self._obj):
            arg_spec = inspect.getfullargspec(self._obj.__init__)
            all_args = arg_spec.args.copy()
            if "self" in all_args:
                all_args.remove("self")
            if arg_spec.defaults is not None:
                positionals = []
                while len(all_args) > len(arg_spec.defaults):
                    positionals.append(all_args.pop(0))
                flags = dict(zip(all_args, arg_spec.defaults))
                self.flag_spec = self._parse_flags(flags)
            else:
                positionals = all_args
            self.positional_spec = self._parse_positionals(positionals)
            self.subcommand_spec = self._parse_subcommands()
        elif isinstance(self._obj, types.FunctionType):
            arg_spec = inspect.getfullargspec(self._obj)
            all_args = arg_spec.args.copy()
            if "self" in all_args:
                all_args.remove("self")
            if arg_spec.defaults is not None:
                positionals = []
                while len(all_args) > len(arg_spec.defaults):
                    positionals.append(all_args.pop(0))
                flags = dict(zip(all_args, arg_spec.defaults))
                self.flag_spec = self._parse_flags(flags)
            else:
                positionals = all_args
            self.positional_spec = self._parse_positionals(positionals)

    def _parse_subcommands(self):
        methods = [m for m in self._obj.__dict__ if not m.startswith("_")]
        subcommand_spec = []
        for method in methods:
            if hasattr(self._obj, method):
                _m = getattr(self._obj, method)
                _e = EasyCLI(_m, execute=False)
                self._sub_map[_e.name] = _m.__name__
                subcommand_spec.append(_e.spec)
        return subcommand_spec

    def _get_valid_shortname(self, name):
        pos = 0
        while len(name) > pos:
            if name[pos] not in self._shortnames:
                self._shortnames.append(name[pos])
                return "-%s" % name[pos]
            pos += 1
        return None

    def _parse_positionals(self, positionals):
        positional_spec = []
        for positional in positionals:
            p = DEFAULT_POSITIONAL_SPEC.copy()
            help_matches = re.findall(rf":param {re.escape(positional)}: (.*)", self.desc)
            ty = self.anno.get(positional, str)
            p["type"] = ty
            p["help"] = ": :".join(help_matches)
            p["name"] = positional
            p["metavar"] = positional.upper()
            if ty is list:
                p["type"] = str
                p["nargs"] = "+"
            if ty not in (str, list, int):
                p["type"] = str
            positional_spec.append(p)
        return positional_spec

    def _parse_flags(self, flags):
        flag_spec = []
        for flag, default in flags.items():
            f = DEFAULT_FLAG_SPEC.copy()
            help_matches = re.findall(rf"\s+:param {re.escape(flag)}: (.*)", self.desc)
            ty = self.anno.get(flag, str)
            f["type"] = ty
            f["help"] = ", ".join(help_matches)
            f["default"] = default
            names = []
            if len(flag) > 1:
                shortname = self._get_valid_shortname(flag)
                if shortname is not None:
                    names.append(shortname)
                names.append("--%s" % flag)
            else:
                names.append("-%s" % flag)
            f["names"] = names
            if ty is bool:
                del f["type"]
                f["action"] = "store_true"
            if ty is list:
                f["type"] = str
                f["nargs"] = "+"
            # Default to STR for unsupported types
            if ty not in (str, list, int, bool):
                f["type"] = str
            flag_spec.append(f)
        return flag_spec

class CLIApp:
    def __init__(self, prefix_path: str = None, app_name: str = "CLIApp"):
        """

        :param prefix_path:
        :param app_name:
        """
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
