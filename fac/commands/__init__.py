import argparse
import textwrap


class CommandRegistry(type):
    commands = []

    def __init__(cls, name, bases, dict):
        super().__init__(name, bases, dict)
        cls.subcommands = []

        if 'parent' in dict:
            dict['parent'].subcommands.append(cls)
        elif 'name' in dict:
            CommandRegistry.commands.append(cls)


class Command(metaclass=CommandRegistry):
    arguments = []
    usage = None
    help = ''
    epilog = ''

    def __init__(self, api, config, manager):
        self.api = api
        self.config = config
        self.manager = manager

    def create_parser(self, subparser, parents):
        doc = self.__doc__ or ''
        description = textwrap.dedent(doc.strip('\n') or self.help)
        epilog = textwrap.dedent(self.epilog.strip('\n'))
        help = self.help or (description and description.splitlines()[0])

        command_parser = argparse.ArgumentParser(add_help=False)
        group = command_parser.add_argument_group('%s options' % self.name)
        for args, kwargs in self.arguments:
            group.add_argument(*args, **kwargs)

        subcommands_parser = argparse.ArgumentParser(add_help=False, usage='%(prog)s ' + self.name)
        if self.subcommands:
            subcommand_parser = subcommands_parser.add_subparsers(
                metavar='SUBCOMMAND',
                title=None,
            )
            for subcommand_class in self.subcommands:
                subcommand = subcommand_class(self.api, self.config, self.manager)
                subcommand.create_parser(subcommand_parser, [command_parser] + parents)

        self.parser = subparser.add_parser(
            self.name,
            usage=self.usage,
            help=help,
            description=description,
            epilog=epilog,
            parents=[subcommands_parser, command_parser] + parents,
            add_help=False,
            formatter_class=argparse.RawDescriptionHelpFormatter,
        )

        self.parser.set_defaults(run=self.run)

    def run(self, args):
        self.parser.print_help()

def Arg(*args, **kwargs):
    return args, kwargs
