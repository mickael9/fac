from fac.commands import Command, Arg


class PackUnpackCommand(Command):
    arguments = [
        Arg('mods', nargs='+', help='mods to affect'),
    ]

    def run(self, args):
        for mod_name in args.mods:
            mod = self.manager.get_mod(mod_name)

            if not mod:
                print('Mod %s does not exist' % mod_name)
                return

            pack = self.name == 'pack'

            if pack == mod.packed:
                print('%s is already %sed' % (mod_name, self.name))
                continue

            if pack:
                mod.pack()
            else:
                mod.unpack()

            print('%s is now %sed' % (mod_name, self.name))

class PackCommand(PackUnpackCommand):
    'Pack mods'

    name = 'pack'


class UnpackCommand(PackUnpackCommand):
    'Unpack mods'

    name = 'unpack'

