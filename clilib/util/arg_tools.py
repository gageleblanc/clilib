import argparse

from clilib.util.decorators import deprecated


class arg_tools:
    """
    Tools for setting up argparse automatically based on a dict specification
    """
    parser = None
    subparsers = {}

    @staticmethod
    @deprecated("You should use spec-based parser generation.")
    def command_parser(module_list):
        parser = argparse.ArgumentParser(add_help=False)
        parser.add_argument("-h", "--help", action="help", help="show this help message and exit")
        parser.add_argument('command', choices=module_list, nargs=argparse.REMAINDER)
        args, _ = parser.parse_known_args()
        if len(args.command) > 0:
            return args, _
        else:
            parser.print_help()
            exit(1)

    @staticmethod
    def build_simple_parser(spec):
        """
        Build simple, one-dimensional parser based on given specification and parse arguments
        :param spec: Parser specification
        :return: Namespace
        """
        parser = argparse.ArgumentParser(description=spec.get("desc", None))
        arg_tools.build_subparser_args(spec, parser)
        arg_tools.parser = parser
        return parser.parse_args()

    @staticmethod
    def build_full_parser(spec):
        """
        Build full parser with subcommands based on given specification without parsing arguments.
        :param spec: Parser specification
        :return:
        """
        parser = argparse.ArgumentParser()
        subparser = parser.add_subparsers(dest='cmd', description=spec['desc'])
        aliases = spec.get("aliases", [])
        parser_baz = subparser.add_parser(spec['name'], help=spec['desc'], description=spec['desc'], aliases=aliases)
        arg_tools.parser = parser
        arg_tools.subparsers[spec["name"]] = parser_baz
        return parser, parser_baz

    @staticmethod
    @deprecated("You should use build_full_cli.")
    def build_full_subparser(spec):
        """
        Build full parser and subparsers based on given specification, and return arguments
        :param spec: Parser specification
        :return: Namespace
        """
        parser, subparser = arg_tools.build_full_parser(spec)
        arg_tools.build_subparser_args(spec, subparser)

        return parser.parse_args()

    @staticmethod
    def build_nested_subparsers(spec):
        parser = argparse.ArgumentParser(add_help=False)
        cmd_subparsers = parser.add_subparsers(dest='cmd', description=spec['desc'])
        cmd_parser = cmd_subparsers.add_parser(spec['name'], help=spec['desc'], description=spec['desc'])
        subcommand_subparser = cmd_parser.add_subparsers(dest='subcmd', description=spec['desc'])
        arg_tools.build_subparser_args(spec, cmd_parser)
        arg_tools.process_subcommands(spec, subcommand_subparser)

        return parser.parse_args()

    @staticmethod
    def build_full_cli(spec):
        """
        Build full command-line application based on specification.
        :param spec: Parser specification
        :return: Namespace
        """
        arg_tools.parser = parser = argparse.ArgumentParser(description=spec.get("desc", ""))
        arg_tools.build_subparser_args(spec, parser)
        subcommands = spec.get("subcommands", [])
        if len(subcommands) > 0:
            cmd_subparsers = parser.add_subparsers(dest="subcommand", description="Available Subcommands")
            arg_tools.process_subcommands(spec, cmd_subparsers)
        return parser.parse_args()

    @staticmethod
    def build_subparser_args(spec, subparser):
        """
        Build arguments for given subparser based on specification.
        :param spec: Parser specification
        :param subparser: Subparser to add arguments to
        :return: None
        """
        for pos in spec['positionals']:
            name = pos["name"]
            del pos["name"]
            subparser.add_argument(name, **pos)

        for flag in spec['flags']:
            names = flag["names"]
            del flag["names"]
            subparser.add_argument(*names, **flag)

    @staticmethod
    def process_subcommands(spec, subcommand_subparser):
        """
        Process given specification and add subcommands to given subparser
        :param spec: Specification to process
        :param subcommand_subparser: Subparser to manipulate
        :return:
        """
        for subcommand in spec['subcommands']:
            subcommand_name = subcommand['name']
            aliases = subcommand.get("aliases", [])
            subcommand_parser = subcommand_subparser.add_parser(subcommand_name, help=subcommand['desc'],
                                                                description=subcommand['desc'],
                                                                aliases=aliases)
            arg_tools.build_subparser_args(subcommand, subcommand_parser)
            sbc = subcommand.get("subcommands", [])
            if len(sbc) > 0:
                subcommand_sp = subcommand_parser.add_subparsers(dest=subcommand['name'], description=spec['desc'])
                arg_tools.process_subcommands(subcommand, subcommand_sp)
