import argparse
import textwrap


class CommandRegistry(type):
    commands = []

    def __init__(cls, name, bases, dict):
        super().__init__(name, bases, dict)
        if 'name' in dict:
            CommandRegistry.commands.append(cls)


class Command(metaclass=CommandRegistry):
    arguments = []
    help = ''

    def __init__(self, api, config, manager):
        self.api = api
        self.config = config
        self.manager = manager

    def create_parser(self, subparser, parents):
        doc = self.__doc__ or ''
        description = textwrap.dedent(doc.strip('\n') or self.help)
        help = self.help or (description and description.splitlines()[0])

        parser = subparser.add_parser(
            self.name,
            help=help,
            description=description,
            parents=parents,
            add_help=False,
            formatter_class=argparse.RawDescriptionHelpFormatter,
        )
        for args, kwargs in self.arguments:
            parser.add_argument(*args, **kwargs)
        parser.set_defaults(run=self.run)


def Arg(*args, **kwargs):
    return args, kwargs
