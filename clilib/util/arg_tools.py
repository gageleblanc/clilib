import argparse


class arg_tools:
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
    def build_full_parser(spec):
        parser = argparse.ArgumentParser()
        subparser = parser.add_subparsers(dest='cmd', description=spec['desc'])
        parser_baz = subparser.add_parser(spec['name'], help=spec['desc'], description=spec['desc'])
        return parser, parser_baz

    @staticmethod
    def build_full_subparser(spec):
        parser, subparser = arg_tools.build_full_parser(spec)
        arg_tools.build_subparser_args(spec, subparser)

        return parser.parse_args()

    @staticmethod
    def build_subparser_args(spec, subparser):
        for pos in spec['positionals']:
            if 'nargs' in pos:
                subparser.add_argument(pos['name'], metavar=pos['metavar'], type=pos['type'], help=pos['help'],
                                       default=pos['default'], nargs=pos['nargs'])
            else:
                subparser.add_argument(pos['name'], metavar=pos['metavar'], type=pos['type'], help=pos['help'],
                                       default=pos['default'])

        for flag in spec['flags']:
            if 'action' in flag:
                if 'store_true' in flag['action']:
                    subparser.add_argument(*flag['names'], help=flag['help'], default=flag['default'],
                                           action=flag['action'], required=flag['required'])
                else:
                    subparser.add_argument(*flag['names'], type=flag['type'], help=flag['help'],
                                           default=flag['default'],
                                           action=flag['action'],
                                           required=flag['required'])
            else:
                subparser.add_argument(*flag['names'], type=flag['type'], help=flag['help'], default=flag['default'],
                                       required=flag['required'])

    @staticmethod
    def process_subcommands(spec, subcommand_subparser):
        subcommand_parsers = {}
        for subcommand in spec['subcommands']:
            subcommand_name = subcommand['name']
            subcommand_parser = subcommand_subparser.add_parser(subcommand_name, help=subcommand['desc'],
                                                                description=subcommand['desc'])
            subcommand_parsers[subcommand_name] = subcommand_parser
            arg_tools.build_subparser_args(subcommand, subcommand_parser)
            if "subcommands" in subcommand:
                subcommand_sp = subcommand_parser.add_subparsers(dest=subcommand['name'], description=spec['desc'])
                arg_tools.process_subcommands(subcommand, subcommand_sp)

    @staticmethod
    def build_nested_subparsers(spec):
        parser = argparse.ArgumentParser(add_help=False)
        cmd_subparsers = parser.add_subparsers(dest='cmd', description=spec['desc'])
        cmd_parser = cmd_subparsers.add_parser(spec['name'], help=spec['desc'], description=spec['desc'])
        subcommand_subparser = cmd_parser.add_subparsers(dest='subcmd', description=spec['desc'])
        arg_tools.build_subparser_args(spec, cmd_parser)
        arg_tools.process_subcommands(spec, subcommand_subparser)

        return parser.parse_args()
