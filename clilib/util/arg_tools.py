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
  def build_full_parser():
    parser = argparse.ArgumentParser()
    parser.add_argument('-d', '--debug', help='Run in debug mode for extended output.', action='store_true', default=False, required=False)
    return parser
