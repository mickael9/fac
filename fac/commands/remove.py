from fac.commands import Command, Arg
from fac.utils import prompt


class RemoveCommand(Command):
    'Remove mods'

    name = 'remove'
    arguments = [
        Arg('mod', help="Mod pattern to remove ('*' for all)", nargs='+'),

        Arg('-y', '--yes', action='store_true',
            help='automatic yes to confirmation prompt'),
    ]

    def run(self, args):
        mods = []
        for mod_pattern in args.mod:
            mods.extend(self.manager.get_mods(mod_pattern))

        if mods:
            print('The following mods will be removed:')
            for mod in mods:
                print('    %s' % mod.location)

            if not args.yes and prompt('Continue?', 'Y/n') != 'y':
                return

            for mod in mods:
                mod.remove()
        else:
            print('No matching mods.')
