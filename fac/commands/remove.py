from fac.commands import Command, Arg
from fac.utils import prompt


class RemoveCommand(Command):
    'Remove mods.'

    name = 'remove'
    arguments = [
        Arg('mods', help="mod patterns to remove ('*' for all)", nargs='+'),

        Arg('-y', '--yes', action='store_true',
            help='automatic yes to confirmation prompt'),

        Arg('-U', '--unpacked', action='store_false', dest='packed',
            default=None, help='only remove unpacked mods'),

        Arg('-P', '--packed', action='store_true', dest='packed',
            default=None, help='only remove packed mods',),
    ]

    def run(self, args):
        mods = []
        for mod_pattern in args.mods:
            mod_pattern = self.manager.resolve_mod_name(mod_pattern)
            matches = self.manager.find_mods(mod_pattern,
                                             packed=args.packed)
            mods.extend(matches)
            if not matches:
                print('No match found for %s.' % mod_pattern)

        if mods:
            print('The following mods will be removed:')
            for mod in mods:
                print('    %s' % mod.location)

            if not args.yes and prompt('Continue?', 'Y/n') != 'y':
                return

            for mod in mods:
                mod.remove()
