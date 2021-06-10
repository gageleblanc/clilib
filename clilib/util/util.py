import logging
import argparse
import sys


class Util:
    @staticmethod
    def dump_module(args, module):
        if args.debug:
            print(dir(module))

    @staticmethod
    def import_test():
        print("Import success!")

    @staticmethod
    def configure_logging(args=None, name=__name__, fmt='[%(asctime)s][%(name)s][%(levelname)8s] - %(message)s'):
        log_formatter = logging.Formatter(fmt=fmt)
        log = logging.getLogger(name)
        if log.hasHandlers():
            return log
        log.setLevel(logging.INFO)
        if args is not None:
            if isinstance(args, argparse.Namespace):
                if "debug" in args:
                    if args.debug:
                        log.setLevel(logging.DEBUG)

        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(log_formatter)
        if args is not None:
            if isinstance(args, argparse.Namespace):
                if "debug" in args:
                    if args.debug:
                        console_handler.setLevel(logging.DEBUG)

        log.addHandler(console_handler)

        return log

    @staticmethod
    def do_confirm(question, default="no"):
        """Ask a yes/no question via raw_input() and return their answer.

        "question" is a string that is presented to the user.
        "default" is the presumed answer if the user just hits <Enter>.
                It must be "yes" (the default), "no" or None (meaning
                an answer is required of the user).

        The "answer" return value is True for "yes" or False for "no".
        """
        valid = {"yes": True, "y": True, "ye": True, "no": False, "n": False}
        if default is None:
            prompt = " [y/n] "
        elif default == "yes":
            prompt = " [Y/n] "
        elif default == "no":
            prompt = " [y/N] "
        else:
            raise ValueError("invalid default answer: '%s'" % default)

        while True:
            sys.stdout.write(question + prompt)
            choice = input().lower()
            if default is not None and choice == "":
                return valid[default]
            elif choice in valid:
                return valid[choice]
            else:
                sys.stdout.write("Please respond with 'yes' or 'no' " "(or 'y' or 'n').\n")
