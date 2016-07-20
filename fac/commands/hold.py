from fac.commands import Command, Arg


class HoldCommand(Command):
    'Hold mods (show held mods with no argument)'

    name = 'hold'
    arguments = [
        Arg('mod', help='Mod to hold', nargs='*'),
    ]

    def run(self, args):
        for name in args.mod:
            installed = self.manager.get_mod_files(name)

            if not installed:
                print('%s is not installed.' % name)
                continue

            if name not in self.config.hold:
                self.config.hold += [name]
                self.config.save()
                print('%s will not be updated automatically anymore' %
                      name)
            else:
                print('%s is already held' % name)
        if not args.mod:
            if self.config.hold:
                print('Mods currently held:')
                for name in self.config.hold:
                    print('    %s' % name)
            else:
                print('No held mods.')


class UnholdCommand(Command):
    'Unhold mods'

    name = 'unhold'
    arguments = [
        Arg('mod', help='Mod to unhold', nargs='+'),
    ]

    def run(self, args):
        for name in args.mod:
            if name in self.config.hold:
                hold = self.config.hold
                hold.remove(name)
                self.config.hold = hold
                self.config.save()
                print('%s will now be updated automatically.' %
                      name)
            else:
                print('%s is not held.' % name)
