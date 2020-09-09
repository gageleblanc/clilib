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
