import logging
import argparse
import sys

from clilib.util.decorators import deprecated
from clilib.util.dict import dict_path
from clilib.util.errors import SchemaException


class Util:
    @staticmethod
    def dump_module(args, module):
        if args.debug:
            print(dir(module))

    @staticmethod
    def import_test():
        print("Import success!")

    @staticmethod
    @deprecated("configure_logging has been replaced with clilib.util.logging.Logging")
    def configure_logging(args=None, name=__name__, fmt='[%(asctime)s][%(name)s][%(levelname)8s] - %(message)s', file_log: bool = False, log_path_prefix: str = "/var/log"):
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

        if file_log:
            log_path = name.split(".")

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


class SchemaValidator:
    """
    Validate dict objects against a given schema.
    """
    def __init__(self, schema: dict, strict: bool = False):
        """

        :param schema: Schema to use for validate method
        :param strict: Ensure all keys are present.
        """
        self.schema = schema
        self.strict = strict

    def validate(self, subject: dict):
        """
        Validate given subject dict against the schema given during initialization. Will raise SchemaException for missing
        keys, and TypeError for improper types.
        :param subject: Subject to analyze against schema
        :return: None
        """
        for key, value_type in self.schema.items():
            if self.strict:
                if key not in subject:
                    raise SchemaException("SchemaValidator: missing key %s" % key)
            value = subject.get(key, None)
            if value is not None:
                if isinstance(value, dict):
                    self._validate_dict(value, key)
                elif not isinstance(value, value_type):
                    raise TypeError("Key '%s' expected to be type '%s' but got type '%s'" % (key, value_type, type(value)))

    def _validate_dict(self, subject: dict, path: str = "."):
        schema = dict_path(self.schema, path)
        for key, value_type in schema.items():
            value = subject.get(key, None)
            if self.strict:
                if key not in subject:
                    raise SchemaException("SchemaValidator: missing key %s" % key)
            if isinstance(value, dict):
                self._validate_dict(value, "%s.%s" % (path, key))
            elif not isinstance(value, value_type):
                raise TypeError("Key '%s' expected to be type '%s' but got type '%s'" % (key, value_type, type(value)))
