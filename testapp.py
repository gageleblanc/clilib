#!/usr/bin/env python3
from clilib.util.logging import Logging
from clilib.builders.app import EasyCLI


class Baz:
    """
    More nesting!
    """
    def __init__(self, debug: bool = False):
        """
        """
        self.debug = debug
        self.logger = Logging("SubcommandClass", debug=debug).get_logger()

    def barry(self, prefix: str = "Default Prefix"):
        """
        Bar Command
        """
        self.logger.info("%s. BarBaz!" % prefix)


class SubcommandClass:
    """
    A subcommand class
    """
    def __init__(self, debug: bool = False):
        """
        """
        self.debug = debug
        self.logger = Logging("SubcommandClass", debug=debug).get_logger()

    def bar(self, prefix: str = "Default Prefix"):
        """
        Bar Command
        """
        self.logger.info("%s. Bar!" % prefix)

    Baz = Baz


class TestApp:
    """
    CLI App for testing EasyCLI
    """
    def __init__(self, debug: bool = False):
        """
        """
        self.debug = debug
        self.logger = Logging("TestApp", debug=debug).get_logger()

    def foo(self, suffix_one: str = "Default Suffix"):
        """
        Foo Command
        """
        self.logger.info("Foo! %s." % suffix_one)

    SubcommandClass = SubcommandClass


if __name__ == "__main__":
    EasyCLI(TestApp)