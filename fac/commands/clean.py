from fac.commands import Command, Arg
from fac.utils import prompt


class CleanCommand(Command):
    """remove old version of mods even if compatible with the game version"""

    name = 'clean'
    arguments = [
        Arg('-y', '--yes', action='store_true',
            help="automatic yes to confirmation prompt"),

        Arg('-U', '--unpacked', action='store_false', dest='packed',
            default=None, help="only remove unpacked mods"),

        Arg('-P', '--packed', action='store_true', dest='packed',
            default=None, help="only remove packed mods",)
        ]
    
    def run(self, args):
        mods = self.manager.find_mods()
        names =sorted([(mod.name,mod.version) for mod in mods])
        to_clean = []
        pointer = (None,None)
        for name in names:
            if name[0] != pointer[0]:
                pointer = name
            else:
                if name[1] < pointer [1]:
                    to_clean += [name]
                else:
                    to_clean += [pointer]
                    pointer = name

        to_clean = [self.manager.get_mod(mod[0], version=mod[1])for mod in to_clean]
        if not to_clean:
            print("No old versions of mods to remove.")
            return
        else:
            print("The following mods will be removed:")
            for mod in to_clean:
                print("    %s" % mod.location)

            if not args.yes and prompt("Continue?", "Y/n") != "y":
                return

            for mod in to_clean:
                mod.remove()
