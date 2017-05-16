fac
===


`Fac` is a command-line mod manager for Factorio >=0.13 written in Python 3.

.. contents::
   :depth: 1

Installation
------------

You'll need Python 3, which can be obtained through your distribution's
package manager or downloaded from https://www.python.org/ (for Windows users).

Installation can be easilly done using pip:

.. code::

    $ pip3 install fac-cli

Or directly from git:

.. code::

    $ pip3 install -e "git+https://github.com/mickael9/fac.git#egg=fac-cli"

Or from an existing clone:

.. code::

    $ pip3 install -e .


*NOTE (linux users)*: By default, these commands will require you to be root unless you
run `pip` from a virtualenv or you use the ``--user`` flag.

If you run `pip` with the ``--user`` flag, make sure ``~/.local/bin`` is in your `PATH`
or the `fac` command will not work.


Configuration
-------------

fac needs to be able to know the location of:

- The Factorio data directory, eg ``/usr/share/factorio/``
- The Factorio configuration directory, eg ``~/.factorio``

Normally, it should be able to detect these automatically assuming you have a standard
setup (eg. Steam).
It will also look in the current working directory and its parent.

If for some reason these paths can't be found automatically, you'll have to specify
them in fac's config file, which is located at:

- ``~/.config/fac/config.ini`` on Linux
- ``C:\Users\<username>\AppData\Local\fac\config.ini`` on Windows
- ``~/Library/Application Support/fac/config.ini`` on Mac OS X

.. code:: ini

    [paths]
    data-path = /home/me/my_factorio/data
    write-path = /home/me/my_factorio

You can display the currently detected locations using ``fac -v``:

.. code::

    $ fac -v
    DEBUG:fac.main:Factorio write path: /home/mickael/.factorio
    DEBUG:fac.main:Factorio game path: /usr/share/factorio
    DEBUG:fac.main:Factorio version: 0.13.9
    usage: fac COMMAND [options...]
    [...]

Usage
-----

`fac` can be run using the `fac` command.
It is further divided into several subcommands:

.. code::

    usage: fac COMMAND [options...]

    Mod manager for Factorio

      COMMAND
        list                List installed mods and their status.
        enable              Enable mods.
        disable             Disable mods.
        search              Search the mods database.
        show                Show details about specific mods.
        install             Install (or update) mods.
        update              Update installed mods.
        remove              Remove mods.
        hold                Hold mods (show held mods with no argument).
        unhold              Unhold mods.
        pack                Pack mods.
        unpack              Unpack mods.
        fetch               Fetch a mod from the mod portal.
        make-compatible     Change the supported factorio version of mods.

    general options:
      -g GAME_VERSION, --game-version GAME_VERSION
                            force a specific game version
      -m MODS_DIRECTORY, --mods-directory MODS_DIRECTORY
                            use the specified mods directory
      -i, --ignore-game-ver
                            ignore game version when selecting packages
      -v, --verbose         show more detailled output
      -h, --help            show this help message and exit


Below are simple examples of what you can do for each command.

Listing installed mods
----------------------

.. code::

    $ fac list
    Installed mods:
        Warehousing 0.0.10
        YARM 0.7.105
        advanced-logistics-system 0.3.0 (unpacked, incompatible)
        creative-mode 0.1.4 (disabled, unpacked)

Enabling & disabling mods
-------------------------

.. code::

    $ fac disable YARM
    YARM is now disabled

    $ fac list
        YARM 0.7.105 (disabled)

    $ fac enable YARM
    YARM is now enabled

    $ fac list
        YARM 0.7.105

Searching for mods
------------------

.. code::

    $ fac search 5dim

    5dim's Mod - Core
        Name: 5dim_core
        Tags: big-mods

        Core of all 5dim's mod

    5dim's Mod - Automatization
        Name: 5dim_automatization
        Tags: big-mods

        Automatization for 5dim's mod

    5dim's Mod - Energy
        Name: 5dim_energy
        Tags: big-mods

        Energy for 5dim's mod

    [...]


Showing detailled info about a mod
----------------------------------

.. code::

    $ fac show 5dim_logistic
    Name: 5dim_logistic
    Author: McGuten
    Title: 5dim's Mod - Logistic
    Summary: logistic of all 5dim's mod
    Description:
        logistic of all 5dim's mod
    Tags: big-mods
    Homepage: http://www.5dim.es
    License: MIT
    Game versions: 0.13
    Releases:
        Version: 0.13.1    Game version: 0.13     
        Version: 0.13.0    Game version: 0.13     

Installing mods
---------------

.. code::

    $ fac install Foreman 5dim_logistic
    Adding dependency: 5dim_core 0.13.1
    Installing: Foreman 0.2.5...
    Downloading: https://mods.factorio.com/api/downloads/data/mods/308/Foreman_0.2.5.zip...
    Installing: 5dim_core 0.13.1...
    Downloading: https://mods.factorio.com/api/downloads/data/mods/191/5dim_core_0.13.1.zip...
    Installing: 5dim_logistic 0.13.1...
    Downloading: https://mods.factorio.com/api/downloads/data/mods/196/5dim_logistic_0.13.1.zip...

    $ fac install Foreman==0.2.2
    Foreman==0.2.5 is already installed. Use -R to reinstall it.

    Foreman is already installed in a more recent version. Use -D to downgrade it.

    $ fac install Foreman==0.2.2 -D
    Installing: Foreman 0.2.2...
    Downloading: https://mods.factorio.com/api/downloads/data/mods/308/Foreman_0.2.2.zip...
    Removing: /home/mickael/.factorio/mods/Foreman_0.2.5.zip

The fetch command can be used to download a mod into a specified directory.

Updating mods
-------------

.. code::

    $ fac update
    Checking: Foreman
    Checking: 5dim_logistic
    Checking: 5dim_core
    Checking: YARM
    Found 1 update:
        Foreman 0.2.2 -> 0.2.3
    Continue? [Y/n] 
    Downloading: https://mods.factorio.com/api/downloads/data/mods/308/Foreman_0.2.3.zip...
    Removing: /home/mickael/.factorio/mods/Foreman_0.2.2.zip

Holding mods
------------
Use this to keep mods from being automatically updated when using the `update` command.

.. code::

    $ fac install Foreman==0.2.2
    Installing: Foreman 0.2.2...
    Downloading: https://mods.factorio.com/api/downloads/data/mods/308/Foreman_0.2.2.zip...

    $ fac hold Foreman
    Foreman will not be updated automatically anymore

    $ fac update
    Checking: Foreman
    Found update: Foreman 0.2.5
    Foreman is held. Use -H to update it anyway.
    No updates were found

    $ fac unhold Foreman
    Foreman will now be updated automatically.

    $ fac update
    Checking: YARM
    Found 1 update:
        Foreman 0.2.2 -> 0.2.5
    Continue? [Y/n] 
    Downloading: https://mods.factorio.com/api/downloads/data/mods/308/Foreman_0.2.5.zip...
    Removing: /home/mickael/.factorio/mods/Foreman_0.2.2.zip

Removing mods
-------------

.. code::

    $ fac remove Foreman
    The following files will be removed:
        /home/mickael/.factorio/mods/Foreman_0.2.3.zip
    Continue? [Y/n] 
    Removing: /home/mickael/.factorio/mods/Foreman_0.2.3.zip

Packing/unpacking mods
----------------------

Mods can be either packed (`name_0.1.zip`) or unpacked (`name_0.1/`) and the game will 
accept both of them.

Keep in mind that the game will refuse to start if there is both a packed and unpacked
version of a mod, or if there are multiple installed versions for any given mod.

.. code::

    $ fac unpack yarm
    Unpacking: /home/mickael/.factorio/mods/YARM_0.7.105.zip
    Removing file: /home/mickael/.factorio/mods/YARM_0.7.105.zip
    YARM is now unpacked

    $ fac pack yarm
    Packing: /home/mickael/.factorio/mods/YARM_0.7.105/
    Removing directory: /home/mickael/.factorio/mods/YARM_0.7.105/
    YARM is now packed


Using wildcards
---------------

Commands that work on locally installed mods can accept wildcards, eg:

.. code::

    $ fac remove '5dim_*'
    The following files will be removed:
        /home/mickael/.factorio/mods/5dim_logistic_0.13.1.zip
        /home/mickael/.factorio/mods/5dim_core_0.13.1.zip
    Continue? [Y/n] 
    Removing: /home/mickael/.factorio/mods/5dim_logistic_0.13.1.zip
    Removing: /home/mickael/.factorio/mods/5dim_core_0.13.1.zip

    $ fac enable '*'
    advanced-logistics-system was already enabled
    Warehousing was already enabled
    YARM was already enabled
    Foreman is now enabled

Note the presence of quotes around filters to prevent the shell from interpreting them.

Mod name autocorrection
-----------------------

Most commands will try to guess the correct name when given inexact mod names.

If the name is a filter (eg `5dim_*`), no attempt to autocorrect will be made.

The following attempts are made to find a match for a given mod name:

- Exact match
- Case-insensitive match
- Partial case-insensitive match if there is no ambiguity.
- For remote commands (install, update...), the search result if there is only one.

For remote commands, a local match will first be attempted at each step.

For instance:

- `yarm` will be converted to `YARM` via the *Case-insensitive match* strategy
- `ya` will either be converted to `YARM` if you have YARM installed
  or fail because there is more than one result to the `fac search ya` command.

Game version incompatibilities
------------------------------

Mods are tied to a specific factorio version (eg 0.13, 0.14) and can only work
with that version. A 0.14 game will refuse to load a mod made for 0.13.

By default, `fac` will autodetect your installed factorio version and use that to filter
the available commands to compatible mods.

In some cases, you might want to disable this filtering using the ``-i`` option.
You can also override the detected game version using ``-g 0.13`` for instance.

A `make-compatible` command is provided. It will automatically unpack a mod and change
its `factorio_version` field to the currently set game version
(autodetected or provided by the `-g` option).

Usage scenario
~~~~~~~~~~~~~~

You're currently running Factorio 0.14 and want to install your favorite mod, `YARM`:

.. code::

    $ fac search YARM
    Note: 1 mods were hidden because they have no compatible game versions. Use -i to show them.

    $ fac search YARM -i
    Yet Another Resource Monitor Fork
        Name: YARM
        Tags: incompatible, info

    This mod helps you to keep track of your mining sites.

Feeling courageous, you want to try it anyway:

.. code::

    $ fac install -i YARM
    [...]

    $ fac make-compatible YARM
    Unpacking: /home/mickael/.factorio/mods/YARM_0.7.105.zip
    Removing file: /home/mickael/.factorio/mods/YARM_0.7.105.zip
    Game version changed to 0.14 for YARM 0.7.105.

You can now use the mod as if it was made for Factorio 0.14.


ZSH completion script
---------------------

If you're using ZSH (and you should be!) you can install the provided completion script
for a better experience.

You'll need to add the `zsh` directory to your `fpath` using something like this in
your ``.zshrc`` :

.. code::

    fpath+=(/path/to/fac/zsh)

If you installed fac using pip as root, the script should automatically be installed in
the right place (``/usr/share/zsh/site-functions``).

With ``pip --user``, you'll need to add this in your ``.zshrc`` :

.. code::

    fpath+=(~/.local/share/zsh/site-functions)

Note: ``compinit`` must be called after `fpath` is changed so you must either put your changes before
``compinit`` or add another ``compinit`` call after changing `fpath`.

Changelog
---------

0.8
    - Added automatic retries of network requests to the API
    - Added pagination options to `search` command:

      - ``-p, --page``: starting page number for the API calls
      - ``-s, --page-size``: maximum number of returned results per page
      - ``-c, --page-count``: maximum number of pages to fetch

    - Fixed Factorio 0.15 compatibility (use booleans in mod-list.json)
    - Fixed ``-m, --mods-directory`` being ignored when loading mod-list.json

0.7
    - Added more friendly error messages when the user doesn't own the game
    - Fixed "AttributeError: 'ZippedMod' object has no attribute 'factorio_version'" (#8)

0.6
    - Added ``-F, --format`` to `list` and `show` commands.
    - Added ``-I, --include`` and ``-E, --exclude`` to `list` commands.
    - Added ``-m, --mods-directory`` option to use a specific mods directory.
    - Added fac version to output when using ``-v, --verbose``.
    - Improved ZSH completion script.
    - Fixed `write-path` and `data-path` being ignored from config.ini
    - Fixed `search` command format string argument.
    - Fixed options parsing to allow general options anywhere in the command line.

0.5
    - Added workaround for 0.14 mods being considered as 0.13 mods.
    - Added a ZSH completion script.
    - Added ``-F, --format`` option to `search` command to customize the output format using format strings.
    - Various bug fixes.

0.4
    - New `pack` and `unpack` commands to work on unpacked mods.
    - New `fetch` command to fetch a mod without installing it.
    - New `make-compatible` command to bump the `factorio_version` of an installed mod.
    - New ``-l, --limit`` option to the `search` command.
    - New ``-g, --game-version`` option to override the detected game version.
    - New ``-i, --ignore-game-ver`` flag to ignore the current game version.
    - Removed ``--force`` flag in favor of the more specfic ``-R, --reinstall``, ``-D, --downgrade``, ``-H, --held``.
    - Accept patterns in `enable`, `pack`, `hold` commands.
    - Resolve partial mod names.
    - Various bug fixes.

0.3
    - Support for mods with spaces in their names.

0.2
    - Add -y flag to update and remove commands.
    - Recursively create config directory.
    - PyPI packaging.

0.1
    - Initial version.
