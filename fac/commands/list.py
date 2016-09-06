from fac.commands import Command, Arg


class ListCommand(Command):
    'List installed mods and their status.'

    _all_tags = ['disabled', 'unpacked', 'held', 'incompatible']

    name = 'list'

    arguments = [
        Arg('-E', '--exclude', metavar='TAG', nargs='+', action='append',
            default=[], choices=_all_tags,
            help='exclude mods having any of the specified tags'),

        Arg('-I', '--include', metavar='TAG', nargs='+', action='append',
            default=[], choices=_all_tags,
            help='only include mods having the specified tags'),

        Arg('-F', '--format',
            help='show installed mods using the specified format string.'),
    ]
    epilog = """
    Available tags: %s

    An optional format string can be specified with the -F flag.
    You can use this if you want to customize the default output format.

    The syntax of format strings is decribed here:
    https://docs.python.org/3/library/string.html#format-string-syntax

    The provided arguments to the format string are:
        mod  : the mod object (see examples)
        tags : the tags as a space-separated string

    Using the default string ('s') specifier on a JSON list or object will
    output valid JSON.

    Some examples:
        {tags}
        {mod.name}          Mod name
        {mod.version}       Mod version
        {mod.game_version}  Supported game version
        {mod.enabled}       Is the mod enabled? (True/False)
        {mod.packed}        Is the mod packed? (True/False)
        {mod.held}          Is the mod held? (True/False)
        {mod.location}      Mod file/directory path
        {mod.info}          info.json content as JSON
        {mod.info.dependencies}
    """ % (', '.join(_all_tags))

    def run(self, args):
        mods = self.manager.find_mods()
        if not mods:
            print('No installed mods.')
            return

        if not args.format:
            if not args.include and not args.exclude:
                print('Installed mods:')
            else:
                print('Matching mods:')

        found = False
        for mod in sorted(mods, key=lambda m: (not m.enabled, m.name)):
            tags = []
            if not mod.enabled:
                tags.append('disabled')
            if not mod.packed:
                tags.append('unpacked')
            if mod.held:
                tags.append('held')
            if mod.game_version != self.config.game_version_major:
                tags.append('incompatible')

            if any(tag in tags for l in args.exclude for tag in l) or \
               any(tag not in tags for l in args.include for tag in l):
                continue

            tags = ', '.join(tags)
            found = True

            if args.format:
                print(args.format.format(
                    mod=mod, tags=tags
                ))
            else:
                if tags:
                    tags = ' (%s)' % tags
                print('    %s %s%s' % (
                    mod.name, mod.version, tags
                ))
        if not found and not args.format:
            print('No matches found.')
