# clilib
---
![](https://img.shields.io/pypi/v/clilib) 
![](https://img.shields.io/pypi/pyversions/clilib) 
![](http://img.shields.io/pypi/l/clilib) 
![](https://github.com/gageleblanc/clilib/actions/workflows/build-publish.yml/badge.svg?branch=master)

clilib is a python library that does some automatic setup for command-line applications as well as includes various 
utilities that can be used in many applications. This can be used to rapidly deploy cli applications in python.

[Full documentation](https://clilib.symnet.io)

### Quickstart

To quickly turn your function or class into a CLI application based on its arguments, defaults, annotations, and docstrings,
you will need a file that looks something like this:
```
from clilib.util.logging import Logging
from clilib.builders.app import EasyCLI


class TestCommand:
    """
    A test command class
    """
    def __init__(self, debug: bool = False):
        """
        :param debug: Add additional debugging output.
        """
        self.debug = debug
        self.logger = Logging("TestCommand", debug=debug).get_logger()

    ...


if __name__ == "__main__":
    e = EasyCLI(TestCommand)
```

For a working example (an application included with the library that uses EasyCLI) check out [clilib.util.wheel](https://github.com/gageleblanc/clilib/blob/master/clilib/util/wheel.py).

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

Some EasyCLI option highlights:
* `enable_logging` (default False) will enable file logging of the CLI generation (by default, to /var/log/clilib/EasyCLI.log)
* `print_return` (default False) will enable printing the return statement of the method your command resolves to.
* `dump_json` (default True) will dump a list or dict return value to json before printing it. (only effective if `print_return` is true)

#### Notes:
You should keep in mind when using EasyCLI that it is built to provide a simple, quick command line application. Some things
to try and remember when using EasyCLI is that you should do your best to adhere to standard python naming conventions [(PEP8),](https://www.python.org/dev/peps/pep-0008/#naming-conventions)
particularly lowercase, underscored method names are best for EasyCLI. EasyCLI will replace underscores in subcommand names
and argument names with hyphens, and will ignore private class methods (methods whose names start with an underscore). 

You may also tell EasyCLI to ignore a method in your class by putting ":easycli_ignore:" in its docstring.

### SearchableDict

SearchableDict is a class that works just like a regular dict with the added functionality of being able to get and set 
values based on simple dot separated pathing.

Example:
```
>>> from clilib.util.dict import SearchableDict
>>> d = SearchableDict()
>>> d.set_path("foo.bar", "baz")
>>> d.get_path("foo.bar")
'baz'
>>> d.get_path("foo.baz", "None!")
'None!'
```