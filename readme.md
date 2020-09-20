# clilib
---
clilib is a python library that does some automatic setup for cli applications. This is can be used to rapidly deploy cli applications in python.

### Quickstart

To start using clilib, you'll need an entry point file that looks like this:

```
#!/usr/bin/python3

from clilib.util.loader import Loader

modules = ['list', 'switch', 'color']
Loader.start_app(modules, "hue_modules")
```
You'll also need a modules folder, in this example I am setting up a cli application to control Philips Hue lights, so my modules package is "hue_modules". List, switch and color are all commands for the cli applications, and also modules of the same name within the modules folder. This makes it easy to add commands as individual modules quickly.

To create a module, you'll need a package within your modules folder and a class named "main" in there. Your directory structure should look like this: 
```
hue_modules
|-- __init__.py
|-- color
|   |-- __init__.py
|   `-- main.py
|-- list
|   |-- __init__.py
|   `-- main.py
`-- switch
    |-- __init__.py
    `-- main.py
```
So when you run `<cmd> color` it will execute code within `hue_modules/color/main.py`. Your main.py will most likely look similar to the below:
```
from clilib.util.util import Util
from clilib.util.arg_tools import arg_tools


class main:
    def __init__(self):
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

    ... Your code here ... 
```
However, setting up a subparser is not necessary. You can simply start executing your own logic as soon as the init function starts, if that works for you.