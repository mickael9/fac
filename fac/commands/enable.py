from fac.commands import Command, Arg


class EnableDisableCommand(Command):
    arguments = [
        Arg('mods', nargs='+', help='Mods to affect'),
    ]

    def run(self, args):
        for mod_name in args.mods:
            mod_info = self.manager.get_mod_info(mod_name)
            mod_json = self.manager.get_mod_json(mod_name)

            if not (mod_info or mod_json):
                print('Mod %s does not exist' % mod_name)
                return

            enabled = self.name == 'enable'
            if not self.manager.set_mod_enabled(mod_name, enabled):
                print('%s was already %sd' % (mod_name, self.name))
            else:
                print('%s is now %sd' % (mod_name, self.name))


class EnableCommand(EnableDisableCommand):
    'Enable mods'

    name = 'enable'


class DisableCommand(EnableDisableCommand):
    'Disable mods'

    name = 'disable'
