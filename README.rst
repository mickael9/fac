fac
===


`Fac` is a command-line mod manager for Factorio 0.13 written in Python 3.

.. contents::

Installation
------------

You'll need Python 3, which can be obtained through your distribution's
package manager or downloaded from https://www.python.org/ (for Windows users).

Installation can be easilly done using pip:

.. code:: bash

    $ pip3 install fac-cli

Or directly from git:

.. code:: bash

    $ pip3 install -e "git+https://github.com/mickael9/fac.git#egg=fac-cli"

Or from an existing clone:

.. code:: bash

    $ pip3 install -e .


*NOTE (linux users)*: By default, these commands will require you to be root unless you run `pip` from a virtualenv or you use the ``--user`` flag.

If you run `pip` with the ``--user`` flag, make sure ``~/.local/bin`` is in your `PATH` or the `fac` command will not work.


Configuration
-------------

fac needs to be able to know the location of:

 * The Factorio data directory, eg ``/usr/share/factorio/``
 * The Factorio configuration directory, eg ``~/.factorio``

Normally, it should be able to detect these automatically assuming you have a standard setup (eg. Steam).
It will also look in the current working directory and its parent.

If for some reason these paths can't be found automatically, you'll have to specify them in fac's config file, which is located at:

 * ``~/.config/fac/config.ini`` on Linux
 * ``C:\Users\<username>\AppData\Local\fac\config.ini`` on Windows
 * ``~/Library/Application Support/fac/config.ini`` on Mac OS X

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
        list         List installed mods and their status
        enable       Enable mods
        disable      Disable mods
        search       Search the mods database
        show         Show details about specific mods
        install      Install (or update) mods
        update       Update installed mods
        remove       Remove mods
        hold         Hold mods (show held mods with no argument)
        unhold       Unhold mods

    general options:
      -v, --verbose  show more detailled output
      -h, --help     show this help message and exit

Below are simple examples of what you can do for each command.

Listing installed mods
----------------------

.. code::

  $ fac list
  Enabled mods:
      YARM

Enabling & disabling mods
-------------------------

.. code::

    $ fac disable YARM
    YARM is now disabled

    $ fac list
    Disabled mods:
        YARM

    $ fac enable YARM
    YARM is now enabled

    $ fac list
    Enabled mods:
        YARM

Searching for mods
------------------

.. code::

    $ fac search 5dim
    5dim_core
        Core of all 5dim's mod

    5dim_automatization
        Automatization for 5dim's mod

    5dim_energy
        Energy for 5dim's mod

    5dim_transport
        Transport for 5dim's mod

    5dim_logistic
        logistic of all 5dim's mod

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
    Installing: Foreman 0.2.3...
    Downloading: https://mods.factorio.com/api/downloads/data/mods/308/Foreman_0.2.3.zip...
    Installing: 5dim_core 0.13.1...
    Downloading: https://mods.factorio.com/api/downloads/data/mods/191/5dim_core_0.13.1.zip...
    Installing: 5dim_logistic 0.13.1...
    Downloading: https://mods.factorio.com/api/downloads/data/mods/196/5dim_logistic_0.13.1.zip...

    $ fac install Foreman==0.2.2
    Foreman is already installed in a more recent version. Use --force to downgrade it.

    $ fac install Foreman==0.2.2 --force
    Installing: Foreman 0.2.2...
    Downloading: https://mods.factorio.com/api/downloads/data/mods/308/Foreman_0.2.2.zip...
    Removing: /home/mickael/.factorio/mods/Foreman_0.2.3.zip


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
    Foreman is held. Use --force to update it anyway.
    No updates were found

    $ fac unhold Foreman
    Foreman will now be updated automatically.

    $ fac update
    Checking: YARM
    Found 1 update:
        Foreman 0.2.2 -> 0.2.3
    Continue? [Y/n] 
    Downloading: https://mods.factorio.com/api/downloads/data/mods/308/Foreman_0.2.3.zip...
    Removing: /home/mickael/.factorio/mods/Foreman_0.2.2.zip

Removing mods
-------------

.. code::

    $ fac remove Foreman
    The following files will be removed:
        /home/mickael/.factorio/mods/Foreman_0.2.3.zip
    Continue? [Y/n] 
    Removing: /home/mickael/.factorio/mods/Foreman_0.2.3.zip

You can also use wildcards:

.. code::

    $ fac remove '5dim_*'
    The following files will be removed:
        /home/mickael/.factorio/mods/5dim_logistic_0.13.1.zip
        /home/mickael/.factorio/mods/5dim_core_0.13.1.zip
    Continue? [Y/n] 
    Removing: /home/mickael/.factorio/mods/5dim_logistic_0.13.1.zip
    Removing: /home/mickael/.factorio/mods/5dim_core_0.13.1.zip

Note the presence of quotes around ``'5dim_*'``, to prevent the shell from interpreting the asterisk.
