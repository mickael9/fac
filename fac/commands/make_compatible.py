from fac.commands import Command, Arg


class MakeCompatibleCommand(Command):
    '''
    Change the supported factorio version of mods.

    This modifies the `factorio_version` field in the mods' info.json file
    to make them compatible with the current game version.

    Packed mods will be unpacked first.
    Unpacked mods will be modified in place.
    '''

    name = 'make-compatible'
    arguments = [
        Arg('mods', nargs='+', help='mods patterns to affect'),
    ]

    def run(self, args):
        game_ver = self.config.game_version_major
        for mod_pattern in args.mods:
            mod_pattern = self.manager.resolve_mod_name(mod_pattern)
            mods = [
                mod.unpack(replace=False)
                for mod in self.manager.find_mods(mod_pattern)
                if mod.game_version != game_ver
            ]

            if not mods:
                print('No match for %s.' % mod_pattern)
                continue

            for mod in mods:
                print('Game version changed to %s for %s %s.' % (
                    game_ver, mod.name, mod.version))

                mod.info.factorio_version = game_ver
                mod.info.save()
