from fac.commands import Command, Arg
from fac.errors import ModNotFoundError
from fac.utils import parse_requirement, start_iter, Requirement, Version


class InstallCommand(Command):
    """
    Install (or update) mods.

    This will install mods matching the given requirements using this format:
        name
        name==version
        name>=version
        name<version
        ...

    If the version is not specified, the latest version will be selected.

    Outdated versions will be replaced.
    """
    name = 'install'

    arguments = [
        Arg('requirements', nargs='*',
            help="requirements to install "
                 '("name", "name>=1.0", "name==1.2", ...)'),

        Arg('-H', '--held', action='store_true',
            help="allow updating held mods"),

        Arg('-R', '--reinstall', action='store_true',
            help="allow reinstalling mods"),

        Arg('-D', '--downgrade', action='store_true',
            help="allow downgrading mods"),

        Arg('-U', '--unpack', action='store_true', default=None,
            help="unpack mods zip files"),

        Arg('-d', '--no-deps', action='store_true',
            help="do not install any dependencies"),
    ]

    def install(self, args, name, release):
        print("Installing: %s %s..." % (
            name, release.version
        ))

        self.manager.install_mod(name, release, unpack=args.unpack)

    def run(self, args):
        to_install = []

        for req in args.requirements:
            name, spec = parse_requirement(req)

            try:
                name = self.manager.resolve_mod_name(name, remote=True)
                req = Requirement(name, spec)
                releases = start_iter(self.manager.resolve_remote_requirement(
                    req, ignore_game_ver=args.ignore_game_ver
                ))
            except StopIteration:
                releases = []
            except ModNotFoundError as ex:
                print("Error: %s" % ex)
                continue

            if not args.held and req.name in self.config.hold:
                print("%s is held. "
                      "Use -H to install it anyway." % (req.name))
                continue

            local_mod = self.manager.get_mod(req.name)

            for release in releases:
                if local_mod:
                    local_ver = local_mod.version
                    release_ver = Version(release.version)

                    if not args.reinstall and release_ver == local_ver:
                        print("%s==%s is already installed. "
                              "Use -R to reinstall it." % (
                                  local_mod.name, local_ver))
                        break

                    elif not args.downgrade and release_ver < local_ver:
                        print(
                            "%s is already installed in a more recent version."
                            " Use -D to downgrade it." % (
                                local_mod.name
                            )
                        )
                        break

                to_install.append((name, release))
                break
            else:
                print("No match found for %s" % (req,))
                continue

        for name, release in to_install:
            self.install(args, name, release)

        if not args.no_deps:
            self.install_deps(args)

    def install_deps(self, args):
        deps = []

        for mod in self.manager.find_mods():
            try:
                deps += mod.info.dependencies
            except AttributeError:
                pass

        deps_to_install = []
        deps_ok = True

        for dep in deps:
            depreq = parse_requirement(dep)

            if depreq.name == 'base':
                continue  # ignore it since it's not like we can install it

            if depreq.name.startswith('?'):
                continue  # ignore optional dependency

            if self.manager.resolve_local_requirement(
                    depreq,
                    ignore_game_ver=args.ignore_game_ver):
                continue
            try:
                # FIXME: we only try the first release here
                release = next(
                    self.manager.resolve_remote_requirement(
                        depreq,
                        ignore_game_ver=args.ignore_game_ver
                    )
                )
            except ModNotFoundError:
                print("Dependency not found: %s" % depreq.name)
                deps_ok = False
                break

            if not release:
                print("Dependency can not be met: %s" % depreq)
                deps_ok = False
                break

            if (depreq.name, release) not in deps_to_install:
                print("Adding dependency: %s %s" % (
                    depreq.name, release.version
                ))
                deps_to_install.append((depreq.name, release))

        if not deps_ok:
            return

        if deps_to_install:
            print("Installing missing dependencies...")
            for name, release in deps_to_install:
                self.install(args, name, release)

            # we may have added new sub-dependencies
            self.install_deps(args)
