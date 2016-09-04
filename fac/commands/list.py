from fac.commands import Command, Arg


class ListCommand(Command):
    'List installed mods and their status.'

    name = 'list'

    arguments = [
        Arg('-F', '--format',
            help='show installed mods using the specified format string.'),
    ]
    epilog = """
    An optional format string can be specified with the -F flag.
    You can use this if you want to customize the default output format.

    The syntax of format strings is decribed here:
    https://docs.python.org/2/library/string.html#format-string-syntax

    The provided arguments to the format string are:
        mod  : the mod object (see examples)
        tags : the tags as a space-separated string

    Using the default string ('s') specifier on a json list or object will
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
    """

    def run(self, args):
        mods = self.manager.find_mods()
        if not mods:
            print('No installed mods.')
            return

        if not args.format:
            print('Installed mods:')

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


            tags = ', '.join(tags)

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
