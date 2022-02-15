import importlib
import argparse
import inspect
import json
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
    """
    Build command line application out of given object if object is a class or function. If the object is a function, the
    arguments without defaults will be positionals and arguments with defaults will be flags. If the object is a class,
    the base arguments are generated from the __init__ function, and any non-private methods are added as subcommands.
    Subclasses are recursively parsed with EasyCLI again, repeating the process described above.
    """
    args: argparse.Namespace
    def __init__(self, obj, execute: bool = True, enable_logging: bool = False, debug: bool = False, log_location: str = "/var/log", print_return: bool = False, dump_json: bool = True):
        """
        Build command line application out of given object
        :param obj: Object to inspect and build application from
        :param execute: Execute application after building. Default is true
        :param enable_logging: Enable file-based logging for generation. This can be useful for development debugging.
        :param debug: Enable additional debugging output.
        :param log_location: Directory to create log file(s) if enabled. Default is /var/log
        :param print_return: Print return value of method executed based on command line arguments. Default is false.
        :param dump_json: Dump return statement to json if it is one of dict or list before printing. Default is true.
        """
        self.logger = Logging("clilib", "EasyCLI", console_log=False, file_log=enable_logging, file_log_location=log_location, debug=debug).get_logger()
        self.print_return = print_return
        self.dump_json = dump_json
        self._obj = obj
        self._isclass = inspect.isclass(obj)
        self._isfunc = isinstance(obj, types.FunctionType)
        self._ismethod = inspect.ismethod(obj)
        if not isinstance(obj, types.FunctionType) and not inspect.isclass(obj):
            raise TypeError("EasyCLI requires class or method type, not %s" % str(type(obj)))
        self.name = obj.__name__.replace("_", "-").lower()
        self.logger.info("EasyCLI analyzing given object: %s" % self.name)
        if obj.__doc__ is None:
            self.logger.fatal("%s: Missing documentation: raising AttributeError" % self.name)
            raise AttributeError("EasyCLI requires that your code is documented so that it can generate help information and ensure argument types. Documentation missing from: %s " % self.name)
        self.desc = obj.__doc__.strip()
        if self._isclass and not hasattr(obj, "__init__"):
            self.logger.fatal("Object is a class, but is missing init method, so exiting ...")
            raise AttributeError("Object is a class, but is missing init method, so exiting ...")
        if self._isclass:
            self.desc += "\n%s" % obj.__init__.__doc__.strip()
        self.anno = {}
        if self._isfunc:
            self.logger.info("Object is function ...")
            self.anno = obj.__annotations__
        elif self._isclass:
            self.logger.info("Object is class ...")
            self.anno = obj.__init__.__annotations__
        self.flag_spec = []
        self.positional_spec = []
        self._shortnames = ["h"]
        self.subcommand_spec = []
        self.sub_map = {}
        if self._isclass:
            self.sub_map["_class"] = self._obj.__name__
        else:
            self.sub_map = self._obj.__name__
        self.spec: SpecBuilder = SpecBuilder(self.name, self._get_help_string())
        self.aliases = re.findall(r':alias (.*):', self.desc)
        if self.aliases is not None:
            for alias in self.aliases:
                self.spec.add_alias(alias)
        self._get_arguments()
        self._setup_argparse()
        if execute:
            self.execute_cli()

    def execute_cli(self):
        """
        Execute generated command-line application. You typically only need to run this if you initialized EazyCLI with
        execute = False
        :return:
        """
        self.logger.info("Executing generated CLI application for [%s]" % self.name)
        self.logger.info("Argparse spec: %s" % str(self.spec.build()))
        if self._isfunc:
            self.args = arg_tools.build_simple_parser(self.spec.build())
            self.logger.info(self.args)
            self._obj(**vars(self.args))
        elif self._isclass:
            self.args = arg_tools.build_full_cli(self.spec.build())
            self.logger.info(self.args)
            if len(self.subcommand_spec) > 0:
                if self.args.subcommand not in self.sub_map:
                    arg_tools.parser.print_help()
                    exit(1)
                self._resolve_subcommand_path("subcommand")
            else:
                self._obj(**self._get_func_kwargs(self._obj))

    def _get_help_string(self):
        desc_lines = self.desc.split("\n")
        final = []
        for l in desc_lines:
            l = l.strip()
            if not l.startswith(":"):
                final.append(l)
        return " ".join(final)

    def _get_func_kwargs(self, obj):
        if self._isclass:
            self.logger.info("object [%s] is class" % self.name)
            arg_spec = inspect.getfullargspec(obj.__init__)
        elif self._ismethod:
            self.logger.info("object [%s] is method" % self.name)
            arg_spec = inspect.getfullargspec(obj)
        elif self._isfunc:
            self.logger.info("object [%s] is function" % self.name)
            arg_spec = inspect.getfullargspec(obj)
        else:
            raise TypeError("Unable to gather arguments from non-class or non-function types, got (%s)" % str(type(obj)))
        arg_spec.args.remove("self")
        arg_dict = {}
        for arg in arg_spec.args:
            arg_dict[arg] = getattr(self.args, arg)
        return arg_dict

    def _resolve_subcommand_path(self, sub: str):
        ins = self._obj(**self._get_func_kwargs(self._obj))
        subcommand_name = sub
        obj = self._obj
        sub_map = self.sub_map
        while inspect.isclass(obj):
            if subcommand_name not in self.args:
                # replace alias
                if isinstance(sub_map, dict):
                    subcommand_name = sub_map["_class"].lower()
            if subcommand_name in self.args:
                subcommand_name = getattr(self.args, subcommand_name)
                if subcommand_name in sub_map:
                    if isinstance(sub_map[subcommand_name], dict):
                        if hasattr(ins, sub_map[subcommand_name]["_class"]):
                            obj = getattr(ins, sub_map[subcommand_name]["_class"])
                            ins = obj(**self._get_func_kwargs(obj))
                            sub_map = sub_map[subcommand_name]
                        else:
                            print("clilib: EasyCLI: unable to find member %s in object %s." % (sub_map[subcommand_name]["_class"], str(ins)))
                            exit(1)
                    elif isinstance(sub_map[subcommand_name], str):
                        if hasattr(ins, sub_map[subcommand_name]):
                            obj = getattr(ins, sub_map[subcommand_name])
                            ins = obj(**self._get_func_kwargs(obj))
                        else:
                            print("clilib: EasyCLI: unable to find member %s in object %s." % (sub_map[subcommand_name], str(ins)))
                            exit(1)
                    else:
                        print("clilib: EasyCLI: unable to decipher subcommand path from given arguments")
                        exit(1)
                else:
                    print("Invalid arguments!")
                    arg_tools.parser.print_help()
                    exit(1)
            else:
                print("Invalid arguments!")
                arg_tools.parser.print_help()
                exit(1)
        else:
            if ins is not None and self.print_return:
                if (isinstance(ins, dict) or isinstance(ins, list)) and self.dump_json:
                    ins = json.dumps(ins)
                print(ins)

    def _setup_argparse(self):
        for flag in self.flag_spec:
            names = flag["names"]
            del flag["names"]
            self.logger.info("Adding flag: %s" % str(flag))
            self.spec.add_flag(*names, **flag)
        for positional in self.positional_spec:
            name = positional["name"]
            del positional["name"]
            self.logger.info("Adding positional: %s" % str(positional))
            self.spec.add_positional(name, **positional)
        for sub in self.subcommand_spec:
            self.logger.info("Adding subcommand: %s" % str(sub))
            self.spec.add_subcommand(sub)

    def _get_arguments(self):
        if self._isclass:
            arg_spec = inspect.getfullargspec(self._obj.__init__)
            self.logger.info("Inspecting class [%s] argument specification: %s" % (self.name, str(arg_spec)))
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
        elif self._isfunc:
            arg_spec = inspect.getfullargspec(self._obj)
            self.logger.info("Inspecting function [%s] argument specification: %s" % (self.name, str(arg_spec)))
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
        self.logger.info("Parsing subcommands from list [%s] for [%s]" % (str(methods), self.name))
        subcommand_spec = []
        for method in methods:
            if hasattr(self._obj, method):
                _m = getattr(self._obj, method)
                self.logger.info("Inspecting method [%s] from [%s]" % (str(_m), self.name))
                if _m.__doc__ is not None:
                    if ":easycli_ignore:" in _m.__doc__:
                        self.logger.info("Docstring for method [%s] contains :easycli_ignore:, so ignoring" % str(_m))
                        continue
                _e = EasyCLI(_m, execute=False)
                method_path = "%s.%s" % (self._obj.__name__, _m.__name__)
                self.sub_map[_e.name] = _e.sub_map
                for alias in _e.spec.aliases:
                    self.sub_map[alias] = _e.sub_map
                self.logger.info("Adding subcommand: [%s] aliases: (%s)" % (_e.name, ", ".join(_e.spec.aliases)))
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
            self.logger.info("Adding positional argument [%s] for [%s]" % (positional, self.name))
            p = DEFAULT_POSITIONAL_SPEC.copy()
            help_matches = re.findall(rf":param {re.escape(positional)}: (.*)", self.desc)
            ty = self.anno.get(positional, str)
            p["type"] = ty
            p["help"] = ", ".join(help_matches)
            p["name"] = positional
            p["metavar"] = positional.upper()
            if ty is list:
                p["type"] = str
                p["nargs"] = "+"
            if ty not in (str, list, int):
                p["type"] = str
            positional_spec.append(p)
        self.logger.info("Positional spec: %s" % str(positional_spec))
        return positional_spec

    def _parse_flags(self, flags):
        flag_spec = []
        for flag, default in flags.items():
            self.logger.info("Adding flag [%s] with default value [%s] to [%s]" % (flag, default, self.name))
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
                names.append("--%s" % flag.replace("_", "-"))
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
        self.logger.info("Flag spec: %s" % str(flag_spec))
        return flag_spec

class CLIApp:
    """
    Manually build command-line application by passing a name for the subcommand and a path for the module to be executed
    as the subcommand.
    """
    def __init__(self, prefix_path: str = None, app_name: str = "CLIApp"):
        """

        :param prefix_path: Prefix to prepend to subcommand paths
        :param app_name: Name of CLI app, used for logging.
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
        """
        Parse command and return arguments
        :return: Namespace object containing parsed arguments
        """
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
        """
        Execute the specified command based on the given arguments
        :param args: Namespace object containing parsed arguments
        :return: Bool
        """
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
        """
        Run generated command-line application.
        :return: None
        """
        # args, _ = arg_tools.command_parser(self.subcommands.keys())
        args = self.command_parser()
        self.logger.debug(args)
        self.execute_command(args)
