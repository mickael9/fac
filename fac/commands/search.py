import sys

from textwrap import fill
from shutil import get_terminal_size

from fac.utils import match_game_version
from fac.commands import Command, Arg


class SearchCommand(Command):
    """Search the mods database."""

    name = 'search'

    arguments = [
        Arg('query', help="search string", default=(), nargs='*'),

        Arg('-d', help="sort results by most downloaded",
            action='store_const',
            dest='sort',
            const='-downloads'),

        Arg('-a', help="sort results alphabetically",
            action='store_const',
            dest='sort',
            const='title'),

        Arg('-u', help="sort results by most recently updated",
            action='store_const',
            dest='sort',
            const='-updated'),

        Arg('--sort',
            help="comma-separated list of sort fields. "
                 "Prefix a field with - to reverse it",
            dest='sort'),

        Arg('-l', '--limit', type=int,
            help="stop after returning that many results"),

        Arg('-F', '--format',
            help="show results using the specified format string."),

        Arg('-S', '--sync', help="Force database sync",
            action='store_true',
            default=None,
            dest='sync'),

        Arg('--no-sync', help="Don't sync database even if it's out of date",
            action='store_false',
            default=None,
            dest='sync'),
    ]

    epilog = """
    SEARCHING

    Search query strings use the whoosh library.

    Full syntax is described here:
    https://whoosh.readthedocs.io/en/latest/querylang.html

    You can search by a specific field, eg `summary:blueprint` matches all mods
    having the word blueprint in their summary.

    Wildcards can also be used, eg `name:bob*` will match all mods having any
    word starting with bob in their name.

    If you don't specify a field, the search will be done on all default fields
    at the same time: owner, name, title and summary

    The valid fields are:
        name: mod name
        owner: mod owner
        title: mod title
        summary: mod summary (not sortable)
        downloads: download count


    FORMAT STRINGS

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

    Note: as a shorthand, you can also use `0` instead of `result`
    """

    def run(self, args):
        sort = args.sort

        if args.sync is None:
            self.db.maybe_update()
        elif args.sync:
            self.db.update()

        # null queries just list all mods in alphabetical order by default
        if not args.query and not sort:
            sort = 'name'

        hidden = 0

        for result in self.db.search(
                query=' '.join(args.query),
                sortedby=sort,
                limit=args.limit):

            tags = []
            if not match_game_version(result.latest_release,
                                      self.config.game_version_major):
                tags.insert(0, 'incompatible')
                if not args.ignore_game_ver:
                    hidden += 1
                    continue

            if args.format:
                print(args.format.format(result, result=result))
            else:
                print(result.title)
                print("    Name: %s" % result.name)

                if tags:
                    print("    Tags: %s" % (", ".join(tags)))

                print()
                print("\n".join(
                    fill(
                        line,
                        width=get_terminal_size()[0] - 4,
                        tabsize=4,
                        subsequent_indent="    ",
                        initial_indent="    ",
                    )
                    for line in result.summary.splitlines()
                ))
                print()
        if hidden:
            print("Note: %d mods were hidden because they have no "
                  "compatible game versions. Use -i to show them." % hidden,
                  file=sys.stderr)
