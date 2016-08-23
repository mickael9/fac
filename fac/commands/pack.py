from fac.commands import Command, Arg


class PackUnpackCommand(Command):
    arguments = [
        Arg('mods', nargs='+', help='mods to affect'),
        Arg('--replace', '-R', action='store_true',
            help='replace existing file/directory when packing/unpacking'),
        Arg('--keep', '-K', action='store_true',
            help='keep existing directory/file after packing/unpacking'),
    ]

    def run(self, args):
        pack = self.name == 'pack'

        for mod_name in args.mods:
            mod_name = self.manager.resolve_mod_name(mod_name)

            mod = self.manager.get_mod(mod_name, packed=not pack)
            if not mod:
                print('Nothing to %s.' % self.name)
                continue

            dup_mod = self.manager.get_mod(mod_name, mod.version, packed=pack)

            if dup_mod and not args.replace:
                print('%s is already %sed. Use -R to replace it.' % (
                    mod_name, self.name
                ))
                continue

            if pack:
                mod.pack(replace=args.replace, keep=args.keep)
            else:
                mod.unpack(replace=args.replace, keep=args.keep)

            print('%s is now %sed' % (mod_name, self.name))


class PackCommand(PackUnpackCommand):
    'Pack mods'

    name = 'pack'


class UnpackCommand(PackUnpackCommand):
    'Unpack mods'

    name = 'unpack'

