
auth_manager tool
*****************

``auth_manager`` is the management tool for pavao-auth. It handles database
setup and administrator account management, connecting directly to the database
without requiring the server to be running.

The tool is installed under ``tools/auth/`` by ``pavao-pkg`` and is invoked
with Python directly:

.. code-block:: console

   $ python tools/auth/auth_manager.py [--config-file FILE] <command>

``--config-file FILE``
   Path to the application configuration file. Defaults to ``application.yml``
   in the current directory.

Setup
=====

Run ``setup`` once before starting the server for the first time. It creates
the ``pavao`` schema and all required tables, seeds the built-in
``PAVAO::ADMIN_ROLE`` role, and writes the current schema version to
``pavao.schema_version``.

.. code-block:: console

   $ python tools/auth/auth_manager.py setup
   Setup complete.

On startup, the supplier reads ``pavao.schema_version`` and compares it against
the version it expects. If the table is missing or the version does not match,
the auth filter stays active but returns **503** on every protected endpoint
until the mismatch is resolved. The server logs a message indicating whether
``setup`` or ``migrate`` needs to be run.

add-admin
=========

Creates an administrator account. Can be run at any time after ``setup``.

.. code-block:: console

   $ python tools/auth/auth_manager.py add-admin (--interactive | --import-file FILE)

``--interactive``
   Prompts for first name, last name, login, password, and whether to force a
   password change on first login. The login field is pre-filled with a
   suggestion derived from the name.

``--import-file FILE``
   Reads the account specification from a YAML file. Useful for automated
   provisioning and CI environments.

Interactive usage
-----------------

.. code-block:: console

   $ python tools/auth/auth_manager.py add-admin --interactive

   Creating new admin...
   First name: Clara
   Last name (can be left blank): Venturini
   User login: clara.venturini
   Password:
   Confirm password:
   Change password on next login [Y/n]? n
   Success!

Passwords are entered without echo. If the login already exists the tool
aborts without modifying anything.

File import
-----------

.. code-block:: console

   $ python tools/auth/auth_manager.py add-admin --import-file admin.yml

The file must contain an ``admin`` section:

.. code-block:: yaml

   admin:
     first_name: Clara
     last_name: Venturini
     login: clara.venturini
     password: hunter12
     change_password: false

``last_name`` and ``change_password`` are optional (default: empty and
``false``). Names are stored in title case regardless of the casing supplied.
