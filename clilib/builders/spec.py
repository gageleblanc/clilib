

class SpecBuilder:
    """
    Generate specification that can be used with arg_tools for easy configuration of argparse
    """
    def __init__(self, name: str, description: str):
        """
        Builds specification for subcommand programmatically, outputs dictionary valid for arg_tools
        :param name: name of subcommand
        :param description: help description for subcommand
        """
        self.name = name
        self.description = description
        self.flags = []
        self.aliases = []
        self.positionals = []
        self.subcommands = []

    def build(self):
        """
        Build and return final specification
        :return: dict
        """
        spec = {
            "name": self.name,
            "desc": self.description,
            "flags": self.flags,
            "aliases": self.aliases,
            "positionals": self.positionals,
            "subcommands": self.subcommands
        }
        return spec

    def add_alias(self, alias: str):
        """
        Adds alias to spec
        :param alias: string
        :return: void
        """
        if alias not in self.aliases:
            self.aliases.append(alias)

    def add_flag(self, *args, **kwargs):
        """
        Adds flag to spec builder
        :param args: list of names for flag
        :param kwargs: kwargs for argparse
        :return: void
        """
        flag = {
            "names": list(args)
        }
        flag.update(kwargs)
        self.flags.append(flag)

    def add_positional(self, name: str, **kwargs):
        """
        Adds positional argument to spec builder
        :param name: name of positional
        :param kwargs: kwargs for argparse
        :return: void
        """
        pos = {
            "name": name
        }
        pos.update(kwargs)
        self.positionals.append(pos)

    def add_subcommand(self, subcommand: "SpecBuilder"):
        """
        Builds another SpecBuilder instance as a subcommand
        :param subcommand: SpecBuilder instance to register as a subcommand for this SpecBuilder instance
        :return: void
        """
        sc = subcommand.build()
        self.subcommands.append(sc)
