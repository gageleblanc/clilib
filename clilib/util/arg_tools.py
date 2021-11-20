import argparse


class arg_tools:
    parser = None
    subparsers = {}

    @staticmethod
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
        parser = argparse.ArgumentParser(description=spec.get("desc", None))
        arg_tools.build_subparser_args(spec, parser)
        arg_tools.parser = parser
        return parser.parse_args()

    @staticmethod
    def build_full_parser(spec):
        parser = argparse.ArgumentParser()
        subparser = parser.add_subparsers(dest='cmd', description=spec['desc'])
        aliases = spec.get("aliases", [])
        parser_baz = subparser.add_parser(spec['name'], help=spec['desc'], description=spec['desc'], aliases=aliases)
        arg_tools.parser = parser
        arg_tools.subparsers[spec["name"]] = parser_baz
        return parser, parser_baz

    @staticmethod
    def build_full_subparser(spec):
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
        arg_tools.parser = parser = argparse.ArgumentParser(description=spec.get("desc", ""))
        cmd_subparsers = parser.add_subparsers(dest="subcommand", description="Available Subcommands")
        arg_tools.build_subparser_args(spec, parser)
        arg_tools.process_subcommands(spec, cmd_subparsers)
        return parser.parse_args()

    @staticmethod
    def build_subparser_args(spec, subparser):
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
