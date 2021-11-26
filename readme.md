# clilib
---
clilib is a python library that does some automatic setup for cli applications. This is can be used to rapidly deploy cli applications in python.

### Quickstart

To quickly turn your function or class into a CLI application based on its arguments, defaults, annotations, and docstrings,
you will need a file that looks something like this:
```
from clilib.util.logging import Logging
from clilib.builders.app import EasyCLI


class TestCommand:
    """
    A test command class
    :param debug: Add additional debugging output.
    """
    def __init__(self, debug: bool = False):
        self.debug = debug
        self.logger = Logging("TestCommand", debug=debug).get_logger()

    def hello(self, target: str):
        """
        Say hello
        :param target: Target for message
        :return:
        """
        self.logger.info("Hello %s" % target)

    def goodbye(self, target: str = "World"):
        """
        Say goodbye
        :param target: Target for message
        :return:
        """
        self.logger.info("Goodbye %s" % target)

    def _this_shouldnt_register(self):
        self.logger.info("oh no!")


if __name__ == "__main__":
    e = EasyCLI(TestCommand)
```
It's that easy! You can now execute this script from the command line, and you'll be able to pass any arguments your class
or function requires. 

EasyCLI will register each non-private method in a class (sans __init__) as a subcommand with the same name whereas the __init__ method defines
the base arguments. Arguments with defaults are added as flags, arguments without defaults are positionals, and any class
within your class is treated as a subcommand (with its own methods being added as subcommands to itself)

EasyCLI requires a docstring in order to populate the help information for your command line application. EasyCLI will fail
without the docstring present. This is intentional, because it makes you document your code more consistently :)

With the above out of the way, EasyCLI will produce something similar to the following when passed a class:
```
usage: testapp.py [-h] [-d] {hello,goodbye} ...

A test command class

optional arguments:
  -h, --help       show this help message and exit
  -d, --debug      Add additional debugging output.

subcommands:
  Available Subcommands

  {hello,goodbye}
    hello          Say hello
    goodbye        Say goodbye
```

#### Notes:
You should keep in mind when using EasyCLI that it is built to provide a simple, quick command line application. Some things
to try and remember when using EasyCLI is that you should do your best to adhere to standard python naming conventions [(PEP8),](https://www.python.org/dev/peps/pep-0008/#naming-conventions)
particularly lowercase, underscored method names are best for EasyCLI. EasyCLI will replace underscores in subcommand names
and argument names with hyphens, and will ignore private class methods (methods whose names start with an underscore). 

### Complex Configuration

If you want to fine-tune your command line options more, you'll need an entry point file that looks like this:

```
from clilib.builders.app import CLIApp

def main():
    test_app = CLIApp()
    # New CLIApp allows for aliases
    test_app.add_subcommand("hello", "path.to.module.cli")
    test_app.add_subcommand("world", "path.to.module.cli")
    test_app.add_subcommand("another", "path.to.another.module")
    test_app.start_app()

if __name__ == "__main__":
    main()

```
A clilib command needs to be the path to a module with a callable attribute 'main' i.e.:
```
path.to.module
|-- __init__.py
|-- cli.py
```
With clilib 3.0, you can use either the `SpecBuilder` or build your argument spec manually, however `SpecBuilder` will
output a format that is valid with arg_tools.

Manually building spec:
```
spec = {
    "name": "hello",
    "desc": "Command containing hello world stuff!",
    "flags": [
        {"names": ["-d", "--debug"], "action": "store_true", "required": False, "default": False, "help": "Print extra debug information"}
    ],
    "positionals": [],
    "subcommands": []
}
```
Using `SpecBuilder` to build spec:
```
spec_builder = SpecBuilder("hello", "Command containing hello world stuff!")
spec_builder.add_flag("-d", "--debug", action="store_true", required=False, default=False, help="Print extra debug information")
```
`SpecBuilder` is also compatible with adding subcommands simply by creating another `SpecBuilder` instance with your subcommmand
configuration

Adding subcommands with `SpecBuilder`:
```
subcommand_builder = SpecBuilder("foo", "fooey")
spec_builder.add_subcommand(subcommand_builder)
```
So when you run `<cmd> hello` it will execute code within `main` from `path.to.module.cli`. Your cli.py (or equivalent)
will most likely look similar to the below:
```
from clilib.util.arg_tools import arg_tools
from clilib.builders.spec import SpecBuilder
from clilib.util.logging import Logging


class TestApp:
    def __init__(self):
        spec_builder = SpecBuilder("hello", "Command containing hello world stuff!")
        # Add alias with spec builder, or manually with in dict
        spec_builder.add_alias("world")
        spec_builder.add_flag("-d", "--debug", action="store_true", required=False, default=False, help="Print extra debug information")
        spec = spec_builder.build()
        args = arg_tools.build_full_subparser(spec)
        self.args = args
        self.logger = Logging("TestApp", debug=self.args.debug).get_logger()
        self.logger.debug(args)
        self.logger.info("Hello World!")

# Run our app
# Any code can go in main(), and doesn't have to be defined in the same file
def main():
    TestApp()
```
You can also manually build your parser if you need more flexibility. Instead of using `build_full_subparser`,
you can use `build_full_parser`, which will return a `parser, subparser` tuple. You can use these to manually
add arguments as shown below:
```
from clilib.util.util import Util
from clilib.util.arg_tools import arg_tools


def main():
    self.command_methods = {
        'off': self.light_off,
        'on': self.light_on
    }
    self.spec = {
        "desc": 'Switch lights on and off. Supported subcommands are: {}'.format(", ".join(self.command_methods.keys())),
        "name": 'switch'
    }
    parser, subparser = arg_tools.build_full_parser(self.spec)
    subparser.add_argument('subcommand', metavar='SUBCOMMAND', help='Subcommand for switch command.', default=False)
    subparser.add_argument('id', metavar='ID', help='ID of the light or group to manipulate', type=int,
                           default=False)
    subparser.add_argument('-d', '--debug', help="Add extended output.", required=False, default=False,
                               action='store_true')
    subparser.add_argument('-g', '--group', help="Switch group instead of light.", required=False, default=False,
                           action='store_true')
    args = parser.parse_args()
    self.args = args
    self.args.logger = Util.configure_logging(args, __name__)
    self.command_methods[args.subcommand]()
```
However, setting up a subparser is not necessary. You can simply start executing your own logic as soon as `main` is
executed, if that works for you.