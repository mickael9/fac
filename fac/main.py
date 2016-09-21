import argparse
import logging

from fac.api import API
from fac.files import Config
from fac.mods import ModManager

import fac.commands.all  # NOQA
from fac.commands import CommandRegistry

log = logging.getLogger(__name__)


def main():
    common_parser = argparse.ArgumentParser(add_help=False)
    common_group = common_parser.add_argument_group('general options')

    common_group.add_argument(
        '-g', '--game-version',
        help='force a specific game version'
    )

    common_group.add_argument(
        '-m', '--mods-directory',
        help='use the specified mods directory'
    )

    common_group.add_argument(
        '-i', '--ignore-game-ver', action='store_true',
        help='ignore game version when selecting packages'
    )

    common_group.add_argument(
        '-v', '--verbose', action='store_true',
        help='show more detailled output'
    )
    common_group.add_argument(
        '-h', '--help', action='help',
        help='show this help message and exit'
    )

    command_parser = argparse.ArgumentParser(add_help=False)
    command_subparsers = command_parser.add_subparsers(
        dest='command', metavar='COMMAND', title=None,
    )

    api = API()
    config = Config()
    manager = ModManager(api=api, config=config)

    for command_class in CommandRegistry.commands:
        command = command_class(api, config, manager)
        command.create_parser(command_subparsers, [common_parser])

    root_parser = argparse.ArgumentParser(
        description='Mod manager for Factorio',
        add_help=False,
        usage='%(prog)s COMMAND [options...]',
        parents=[command_parser, common_parser]
    )

    args = root_parser.parse_args()

    # Allow common options both before and after command
    common_parser.parse_known_args(namespace=args)

    if args.verbose:
        logging.basicConfig(level=logging.DEBUG)

    if args.game_version:
        config.game_version = args.game_version

    if args.mods_directory:
        config.mods_directory = args.mods_directory

    log.debug('fac version: %s' % fac.__version__)
    log.debug('Factorio write path: %s', config.factorio_write_path)
    log.debug('Factorio game path: %s', config.factorio_data_path)
    log.debug('Mods directory: %s', config.mods_directory)
    log.debug('Factorio version: %s', config.game_version)

    if args.command:
        try:
            args.run(args)
        except KeyboardInterrupt:
            pass
    else:
        root_parser.print_help()

if __name__ == '__main__':
    main()
