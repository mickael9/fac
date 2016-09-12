import sys

from fac.commands import Command, Arg
from textwrap import fill
from shutil import get_terminal_size


class SearchCommand(Command):
    'Search the mods database.'

    name = 'search'

    arguments = [
        Arg('query', help='search string', nargs='?'),

        Arg('-t', help='filter by tag', nargs='*', dest='tag', default=[]),

        Arg('-d', help='sort results by most downloaded',
            action='store_const',
            dest='sort',
            const='top',
            default='top'),

        Arg('-a', help='sort results alphabetically',
            action='store_const',
            dest='sort',
            const='alpha'),

        Arg('-u', help='sort results by most recently updated',
            action='store_const',
            dest='sort',
            const='updated'),

        Arg('-l', '--limit', type=int,
            help='only show that many results'),

        Arg('-F', '--format',
            help='show results using the specified format string.'),
    ]

    epilog = """
    An optional format string can be specified with the -F flag.
    You can use this if you want to customize the default output format.

    The syntax of format strings is decribed here:
    https://docs.python.org/3/library/string.html#format-string-syntax

    There is only one argument passed to the format string which is the
    result object returned by the API.

    Using the default string ('s') specifier on a JSON list or object will
    output valid JSON.

    Some examples:
        {result.name}                   Name of the mod
        {result}                        JSON-repesentation of the result object
        {result.latest_release.version} Latest release version
    """

    def run(self, args):
        hidden = 0
        count = 0
        game_ver = self.config.game_version_major

        for result in self.api.search(
                query=args.query or '',
                tags=tuple(args.tag),
                order=args.sort):

            tags = [tag.name for tag in result.tags]

            # apparently game_versions can't be trusted so cheat a bit here
            if game_ver not in result.game_versions and (
                    game_ver != result.latest_release.factorio_version):
                if args.ignore_game_ver:
                    tags.insert(0, 'incompatible')
                else:
                    hidden += 1
                    continue

            if args.format:
                print(args.format.format(result, result=result))
            else:
                print(result.title)
                print('    Name: %s' % result.name)

                if tags:
                    print('    Tags: %s' % (', '.join(tags)))

                print()
                print('\n'.join(
                    fill(
                        line,
                        width=get_terminal_size()[0] - 4,
                        tabsize=4,
                        subsequent_indent='    ',
                        initial_indent='    ',
                    )
                    for line in result.summary.splitlines()
                ))
                print()

            count += 1
            if args.limit and count >= args.limit:
                break

        if hidden:
            print('Note: %d mods were hidden because they have no '
                  'compatible game versions. Use -i to show them.' % hidden,
                  file=sys.stderr)
