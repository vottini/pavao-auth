
create-admin tool
*****************

The ``create-admin`` tool bootstraps the first administrator account, or adds
additional ones at any time. It connects directly to the database, so the
server does not need to be running — though it must have been started at least
once with pavao-auth loaded and enabled so that the required schema is in place.

The tool is installed under ``tools/auth/`` by ``pavao-pkg`` and is invoked
with Python directly:

.. code-block:: bash

   python tools/auth/create_admin.py [--config-file FILE] (--create-admin | --import-admin FILE)

Options
=======

``--config-file FILE``
   Path to the application configuration file. Defaults to ``application.yml``
   in the current directory.

``--create-admin``
   Interactive mode. Prompts for first name, last name, login, password, and
   whether to force a password change on first login. The login field is
   pre-filled with a suggestion derived from the name.

``--import-admin FILE``
   Non-interactive mode. Reads the account specification from a YAML file.
   Useful for automated provisioning and CI environments.

Interactive usage
=================

.. code-block:: bash

   python tools/auth/create_admin.py --create-admin

   Creating new admin...
   First name: Clara
   Last name (can be left blank): Venturini
   User login: clara.venturini
   Password:
   Confirm password:
   Change password on next login [Y/n]? n
   Success!

The login field is pre-filled with ``first.last`` in lowercase. It can be
edited before confirming. Passwords are entered without echo.

File import
===========

For scripted or repeatable setups, pass a YAML file with ``--import-admin``:

.. code-block:: bash

   python tools/auth/create_admin.py --import-admin admin.yml

The file must contain an ``admin`` section:

.. code-block:: yaml

   admin:
     first_name: Clara
     last_name: Venturini
     login: clara.venturini
     password: S3cr3tPass
     change_password: false

``last_name`` and ``change_password`` are optional (default: empty and
``false``). Names are stored in title case regardless of the casing supplied.
If the login already exists the tool aborts without modifying anything.
