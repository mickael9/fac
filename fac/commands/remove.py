from fac.commands import Command, Arg
from fac.utils import prompt


class RemoveCommand(Command):
    'Remove mods'

    name = 'remove'
    arguments = [
        Arg('mod', help="Mod pattern to remove ('*' for all)", nargs='+'),
    ]

    def run(self, args):
        files = []
        for mod_name in args.mod:
            files += self.manager.get_mod_files(mod_name)

        if files:
            print('The following files will be removed:')
            for file in files:
                print('    %s' % file)
            if prompt('Continue?', 'Y/n') != 'y':
                return

            for mod_name in args.mod:
                self.manager.uninstall_mod(mod_name)
        else:
            print('No matching files.')
