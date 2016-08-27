from fac.commands import Command, Arg


class PackUnpackCommand(Command):
    arguments = [
        Arg('mods', nargs='+', help='mods patterns to affect'),
        Arg('-R', '--replace', action='store_true',
            help='replace existing file/directory when packing/unpacking'),
        Arg('-K', '--keep', action='store_true',
            help='keep existing directory/file after packing/unpacking'),
    ]

    def run(self, args):
        pack = self.name == 'pack'

        for mod_pattern in args.mods:
            mod_pattern = self.manager.resolve_mod_name(mod_pattern)
            mods = self.manager.find_mods(mod_pattern, packed=not pack)

            if not mods:
                print('No %sable found for %s.' % (self.name,
                                                   mod_pattern))
                continue

            for mod in mods:
                dup_mod = self.manager.get_mod(mod.name, mod.version,
                                               packed=pack)

                if dup_mod and not args.replace:
                    print('%s is already %sed. Use -R to replace it.' % (
                        mod.name, self.name
                    ))
                    continue

                if pack:
                    mod.pack(replace=args.replace, keep=args.keep)
                else:
                    mod.unpack(replace=args.replace, keep=args.keep)

                print('%s is now %sed' % (mod.name, self.name))


class PackCommand(PackUnpackCommand):
    'Pack mods.'

    name = 'pack'


class UnpackCommand(PackUnpackCommand):
    'Unpack mods.'

    name = 'unpack'
