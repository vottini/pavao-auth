
Authentication and Authorization
*********************************

pavao-auth adds JWT-based authentication and role-based access control to a pavao
application. It is delivered as a pavao extension: its foundation directory
(``foundation/auth/``) provides a supplier and a filter; its modules directories
(``modules/auth/`` and ``modules/admin/``) provide the user-facing endpoints.

Once installed and enabled, every incoming request passes through the auth filter before
reaching the endpoint processor. Public endpoints opt out of the filter explicitly;
everything else requires a valid access token, and endpoints that declare a
``functionality`` key additionally require a role that has been granted access to it.

Setup
=====

Add the following block to ``application.yml``:

.. code-block:: yaml

   pavao:
     auth:
       enabled: true

     token:
       issuer: myapp.example.com
       validity:
         access_minutes: 30
         refresh_minutes: 2880

     database:
       postgresql:
         host: localhost
         database: mydb
         user: myuser
         password: ${DB_PASSWORD}

On first startup, the supplier runs the SQL scripts in ``foundation/auth/database/``
to create the ``pavao`` schema and its tables. It also seeds the built-in
``PAVAO::ADMIN_ROLE`` role. If the tables already exist the scripts are idempotent.

To create the initial administrator account run the setup tool (or insert a row directly):

.. code-block:: console

   $ python tools/setup.py clara.yml

``clara.yml`` (or any YAML you pass) describes the first admin user:

.. code-block:: yaml

   admin:
     first_name: Clara
     last_name: Venturini
     login: clara.venturini
     password: hunter12
     change_password: true

The password is hashed with Argon2 before storage; the plaintext is never persisted.
Setting ``change_password: true`` forces the user to change their password on first login
before receiving a token with their actual roles.

Injectables
===========

The supplier exposes four named parameters to any endpoint or task that declares them:

.. list-table::
   :header-rows: 1
   :widths: 20 20 60

   * - Name
     - Type
     - Description
   * - ``auth_data``
     - ``AuthData | None``
     - Decoded token claims for the authenticated request. ``None`` when the endpoint
       is public. Fields:

       - ``account_id`` (``str``) — the account identifier from the ``sub`` claim.
       - ``jti`` (``str``) — the token's unique identifier, useful for
         blacklisting on logout or marking a session as modified.
       - ``expiration`` (``int``) — token expiry as a Unix timestamp.

Authentication flow
===================

Login
-----

``POST /login``

.. code-block:: json

   {
     "login": "clara.venturini",
     "password": "hunter12"
   }

The endpoint verifies the password with Argon2, checks that the account is active, and
issues an access token and a refresh token.

If ``change_password`` is set on the account, the access token is issued with an empty
roles claim. The response body includes ``"change_password": true`` to signal that the
client should redirect the user to the password change screen before continuing.

**Response 200:**

.. code-block:: json

   {
     "access_token": "<access_jwt>",
     "token_type": "Bearer",
     "expires_in": 600,
     "change_password": false
   }

The refresh token is returned as an ``HttpOnly``, ``SameSite=Strict`` cookie scoped to
``/refresh-token``, and is never exposed in the response body.

**Errors:**

- 401: Invalid credentials or disabled account (3-second enforced delay to slow brute-force)

Initial password change
-----------------------

Newly created accounts have the ``change_password`` flag set. The initial access token
carries empty roles, so the user can only reach endpoints that do not require a
functionality check. The expected flow is:

1. Client calls ``POST /login`` → receives token with ``"change_password": true``
2. Client calls ``POST /change-password`` with old and new passwords
3. ``authorizer.mark_modified()`` is called, invalidating the initial token
4. Client calls ``POST /login`` again → receives token with actual roles

Token refresh
-------------

``POST /refresh-token``

This endpoint is **public** — it does not require an ``Authorization`` header. It reads
the refresh token from the cookie set during login.

The endpoint validates the token signature, looks up the refresh record in the database
(stored as an MD5 hash of the JTI), verifies it has not expired, and then issues new
access and refresh tokens in a single atomic operation: the old refresh record is deleted
and the new one is inserted. Replaying a used refresh token therefore fails.

**Response 200:**

.. code-block:: json

   {
     "access_token": "<new_access_jwt>",
     "token_type": "Bearer",
     "expires_in": 600
   }

**Errors:** 400 — missing cookie, invalid token, expired token, or disabled account.

Logout
------

``DELETE /logout``

Blacklists the current access token (stored in the in-memory blacklist keyed by
``(account_id, jti)``) and deletes the refresh token record from the database. The
refresh token cookie is cleared in the response.

After logout, the access token remains structurally valid until its ``exp`` claim passes,
but the blacklist entry prevents it from being used. The in-memory blacklist is pruned
daily by the ``clear_blacklist`` task.

**Response:** 204 No Content.

Password change
---------------

``POST /change-password``

.. code-block:: json

   {
     "oldPassword": "hunter12",
     "newPassword": "hunter13"
   }

Verifies the old password, updates the Argon2 hash, and calls
``authorizer.mark_modified(account_id)``. This records the current timestamp against the
user; any token whose ``iat`` (issued-at) is older than that timestamp will be rejected
with a 401 on the next request, forcing re-login.

**Errors:** 400 — old password invalid, or old and new passwords are identical.

Self
----

``GET /self``

Returns the authenticated user's profile and the full list of functionalities they have
access to, translated to the locale indicated by the ``Accept-Language`` header.

**Response 200:**

.. code-block:: json

   {
     "id": 1,
     "firstName": "Clara",
     "lastName": "Venturini",
     "administrator": true,
     "accesses": [
       {
         "package": "Administration",
         "functionality": "List users"
       }
     ]
   }

Protecting endpoints
====================

Any endpoint in the application is protected by default once the filter is enabled.
The filter rejects requests that do not carry a valid token. To further restrict an
endpoint to users with a specific role, add ``package`` and ``functionality`` keys to
the endpoint descriptor:

.. code-block:: python

   def pavao_endpoint():
       return {
           'method': 'GET',
           'path': '/reports/summary',
           'package': 'Reporting',
           'functionality': 'View summary',
           'processor': process
       }

The first time pavao loads this module, the filter calls ``register_functionality()``,
which upserts the ``(package, functionality)`` pair in the database. An administrator can
then grant a role access to it through the admin API. On subsequent restarts, the
``setup()`` call in the supplier's ``initialize()`` reloads all grants from the database,
so previously-configured permissions survive restarts.

Public endpoints
================

Endpoints that should be reachable without a token declare ``'public': True`` in the
descriptor:

.. code-block:: python

   def pavao_endpoint():
       return {
           'method': 'GET',
           'path': '/status',
           'public': True,
           'processor': process
       }

The filter skips public endpoints entirely. ``auth_data`` will be ``None`` for them.

Filter responses
================

When a request is rejected, the filter sets the response status and returns without
calling the processor:

.. list-table::
   :header-rows: 1
   :widths: 10 90

   * - Status
     - Condition
   * - 401
     - Missing ``Authorization`` header, malformed token, invalid signature, expired
       token, token issued before ``mark_modified`` timestamp, or blacklisted token.
   * - 403
     - Token is valid but the user's roles do not include access to the endpoint's
       declared functionality.
   * - 410
     - The functionality has been disabled at runtime by an administrator.

Token invalidation
==================

Three independent mechanisms can invalidate a token before its natural expiry:

**Blacklist (logout)**
  ``authorizer.blacklist(auth_data)`` stores the ``(account_id, jti)`` pair in memory.
  Any subsequent request carrying that token is rejected with 401. Entries are removed
  by the ``clear_blacklist`` task once the token's ``exp`` has passed.

**User modification timestamp**
  ``authorizer.mark_modified(user_id)`` records the current time against the user.
  The filter rejects tokens with ``iat < modification_time``, so all tokens issued before
  the modification (on any device) become invalid simultaneously. Used on password change
  and on role assignment changes.

**Key rotation**
  When the signing key is rotated, tokens issued with the old key remain valid only until
  the key's grace period expires. See :doc:`jwt` for rotation details. A server restart
  (which generates a new key) invalidates all tokens unless a grace period was configured
  beforehand.

Scheduled tasks
===============

Three tasks run automatically:

.. list-table::
   :header-rows: 1
   :widths: 30 20 50

   * - Task
     - Schedule
     - Action
   * - Refresh secret key
     - Daily at midnight
     - Rotates the JWT signing key, keeping the previous key valid for 5 days.
   * - Purge expired tokens
     - Hourly
     - Deletes expired rows from ``pavao.refresh_token``.
   * - Clear blacklist
     - Daily at midnight
     - Removes expired entries from the in-memory token blacklist.

All three tasks are visible and controllable through the admin task management endpoints.
