from fac.commands import Command, Arg


class HoldCommand(Command):
    'Hold mods (show held mods with no argument).'

    name = 'hold'
    arguments = [
        Arg('mods', help='mods patterns to hold', nargs='*'),
    ]

    def run(self, args):
        for mod_pattern in args.mods:
            mod_pattern = self.manager.resolve_mod_name(mod_pattern)
            mods = self.manager.find_mods(mod_pattern)

            if not mods:
                print('No match found for %s.' % mod_pattern)
                continue

            for mod in mods:
                if not mod.held:
                    mod.held = True
                    print('%s will not be updated automatically anymore.' %
                          mod.name)
                else:
                    print('%s is already held' % mod.name)

        if not args.mods:
            if self.config.hold:
                print('Mods currently held:')
                for name in self.config.hold:
                    print('    %s' % name)
            else:
                print('No held mods.')


class UnholdCommand(Command):
    'Unhold mods.'

    name = 'unhold'
    arguments = [
        Arg('mods', help='mods to unhold', nargs='+'),
    ]

    def run(self, args):
        for mod_pattern in args.mods:
            mod_pattern = self.manager.resolve_mod_name(mod_pattern)
            mods = [mod.name for mod in self.manager.find_mods(mod_pattern)]

            if not mods:
                # Special case for mods that have been removed
                # but are still in the hold list
                if mod_pattern in self.config.hold:
                    mods = [mod_pattern]
                else:
                    print('No match found for %s.' % mod_pattern)
                    continue

            for mod_name in mods:
                if self.manager.set_mod_held(mod_name, False):
                    print('%s will now be updated automatically.' %
                          mod_name)
                else:
                    print('%s is not held.' % mod_name)
