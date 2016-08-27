from fac.commands import Command, Arg


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
    ]

    def run(self, args):
        hidden = 0

        for result in self.api.search(
                query=args.query or '',
                tags=tuple(args.tag),
                order=args.sort,
                limit=args.limit):

            tags = [tag.name for tag in result.tags]
            if self.config.game_version_major not in result.game_versions:
                if args.ignore_game_ver:
                    tags.insert(0, 'incompatible')
                else:
                    hidden += 1
                    continue

            if tags:
                tags = ' [%s]' % (', '.join(tags))
            else:
                tags = ''

            print('%s (%s)%s\n    %s\n' % (
                result.title, result.name,
                tags,
                result.summary.replace('\n', '')))

        if hidden:
            print('Note: %d mods were hidden because they have no '
                  'compatible game versions. Use -i to show them.' % hidden)
