
Administration API
******************

The admin module exposes endpoints for managing users, roles, functionalities, and
scheduled tasks at runtime. Every admin endpoint requires the caller to have the
built-in ``PAVAO::ADMIN_ROLE`` role.

The ``@assert_admin_access`` decorator handles this automatically: it wraps the
``pavao_endpoint()`` descriptor function, calls ``authorizer.assert_role_access()``
during registration, and seeds the in-memory permission cache at startup. No manual
database setup is needed.

Error messages are localized via the ``Accept-Language`` header. Supported locales:
``en_US``, ``pt_BR``, ``it_IT``.

Users
=====

``GET /admin/check-login?login={login}``
  Returns ``true`` if the login string is syntactically valid (pattern
  ``^[a-z][a-z0-9]*(?:\.[a-z0-9]+)?$``) and not already taken, ``false`` otherwise.

``POST /admin/users``
  Create a new user.

  .. code-block:: json

     {
       "login": "john.doe",
       "password": "hunter12",
       "firstName": "John",
       "lastName": "Doe",
       "change_password": true
     }

  Returns the new user's integer ID with status 201. Setting ``change_password: true``
  forces a password reset on first login (see :doc:`authentication`). First and last name
  are stored in title case. **409** if the login is already taken.

``GET /admin/users``
  List all users except the authenticated caller.

  .. code-block:: json

     [
       {
         "id": 1,
         "login": "john.doe",
         "firstName": "John",
         "lastName": "Doe",
         "active": true,
         "admin": false
       }
     ]

``GET /admin/users/{user:int}``
  Retrieve a single user with their role assignments.

  .. code-block:: json

     {
       "id": 1,
       "login": "john.doe",
       "firstName": "John",
       "lastName": "Doe",
       "active": true,
       "admin": false,
       "roles": [
         { "id": 3, "name": "Analyst" }
       ]
     }

  The admin role is filtered from the ``roles`` array and reflected in the ``admin``
  flag instead. **404** if the user does not exist.

``PATCH /admin/users/{userId:int}``
  Update login, first name, or last name (all fields optional).

  .. code-block:: json

     {
       "login": "john.doe2",
       "firstName": "Jonathan"
     }

  **404** if user not found. **409** if the new login is already taken.

``POST /admin/users/{user:int}/change-password``
  Set a user's password as an administrator (no current password required).

  .. code-block:: json

     {
       "password": "hunter13",
       "change_password": false
     }

  ``change_password`` is optional and updates the reset flag when provided.
  **404** if user not found.

User activation
---------------

``PUT /admin/users/{user:int}/active``
  Activate a disabled user. **204** on success, **404** if not found.

``DELETE /admin/users/{user:int}/active``
  Deactivate a user (prevents login). Returns **403** if the caller attempts to
  deactivate their own account. **204** on success, **404** if not found.

Admin privileges
----------------

``PUT /admin/users/admins/{user:int}``
  Grant the ``PAVAO::ADMIN_ROLE`` to a user. **204** on success.

``DELETE /admin/users/admins/{user:int}``
  Revoke the admin role from a user. **403** if the caller tries to revoke their own
  admin status. **204** on success, **404** if not found.

``PUT /admin/users/admins``
  Replace the full admin roster with a list of user IDs.

  .. code-block:: json

     [1, 5, 7]

  The authenticated caller is always appended to the list before processing, so it is
  impossible to accidentally remove yourself. All other users not in the list lose the
  admin role.

Role assignments
----------------

``GET /admin/users/{user:int}/assignments``
  List all roles with an ``assigned`` flag for the user.

  .. code-block:: json

     {
       "id": 1,
       "login": "john.doe",
       "firstName": "John",
       "lastName": "Doe",
       "active": true,
       "assignments": [
         { "id": 2, "name": "Analyst", "assigned": true },
         { "id": 3, "name": "Reporter", "assigned": false }
       ]
     }

  **404** if user not found.

``PUT /admin/users/{user:int}/assignments``
  Replace the user's role assignments with a list of role IDs.

  .. code-block:: json

     [2, 4]

  All previously assigned roles not in the list are revoked. Calls
  ``authorizer.mark_modified()`` so existing tokens for the user are invalidated on
  the next request. **404** if user not found.

Roles
=====

``POST /admin/roles``
  Create a new role.

  .. code-block:: json

     {
       "name": "Analyst",
       "description": "Read-only analytics access",
       "code": "USER::ANALYST"
     }

  ``description`` and ``code`` are optional. If ``code`` is omitted it is generated from
  the name: uppercased, non-letter characters removed, spaces replaced with underscores,
  prefixed with ``USER::``. Returns the new role ID with status 201. **409** if the code
  already exists.

``GET /admin/roles``
  List all roles.

  .. code-block:: json

     [
       {
         "id": 2,
         "name": "Analyst",
         "description": "Read-only analytics access"
       }
     ]

``GET /admin/roles/{role:int}``
  Retrieve a single role with its assigned functionalities and users.

  .. code-block:: json

     {
       "id": 2,
       "name": "Analyst",
       "description": null,
       "functionalities": [
         { "id": 5, "package": "Reporting", "name": "View summary" }
       ],
       "users": [
         { "id": 1, "fullName": "John Doe" }
       ]
     }

  **404** if role not found.

``PATCH /admin/roles/{role:int}``
  Update a role's name or description (both optional). **404** if not found.
  **409** if the new name is already taken.

``DELETE /admin/roles/{roleId:int}``
  Delete a role. **204** on success, **404** if not found.

``PUT /admin/roles/{role:int}/assignments``
  Replace the set of users assigned to a role.

  .. code-block:: json

     [1, 4, 7]

  Users not in the list lose the role. **404** if role not found.

Role access
-----------

``GET /admin/roles/{role:int}/accesses``
  List all known functionalities split into two groups for the role.

  .. code-block:: json

     {
       "id": 2,
       "name": "Analyst",
       "accessable": [
         { "id": 5, "package": "Reporting", "name": "View summary" }
       ],
       "forbidden": [
         { "id": 6, "package": "Reporting", "name": "Export data" }
       ]
     }

``PUT /admin/roles/{role:int}/access/{functionality:int}``
  Grant the role access to the functionality. Updates the in-memory cache immediately
  so the change takes effect for the next request without a restart.
  **404** if role not found.

``DELETE /admin/roles/{role:int}/access/{functionality:int}``
  Revoke the role's access to the functionality. Updates the in-memory cache.
  **404** if role not found.

Functionalities
===============

Functionalities are registered automatically the first time an endpoint with a
``package`` and ``functionality`` descriptor key is loaded. They do not need to be
created manually.

``GET /admin/functionalities``
  List all known functionalities grouped by package, with enabled/disabled status.
  Names are translated to the caller's preferred locale.

  .. code-block:: json

     [
       {
         "package": "Reporting",
         "functionalities": [
           {
             "id": 5,
             "functionality": "View summary",
             "enabled": true
           }
         ]
       }
     ]

``GET /admin/functionalities/allowed?roles=[1,2]``
  List functionalities accessible to the given role IDs.

  .. code-block:: json

     [
       {
         "package": "Reporting",
         "functionality": "View summary",
         "allowingRole": "Analyst"
       }
     ]

``PUT /admin/functionalities/{functionality:int}/enable``
  Re-enable a previously disabled functionality. Updates the in-memory disabled set.
  **404** if not found.

``PUT /admin/functionalities/{functionality:int}/disable``
  Disable a functionality globally: all requests to endpoints that declare it will
  receive **410** regardless of the caller's roles. **403** if the admin role still has
  access (the admin grant must be revoked first). **404** if not found.

Tasks
=====

pavao-auth exposes a full task management UI over HTTP. Tasks are the scheduled
background jobs defined across all loaded modules — including third-party extensions.

``GET /admin/tasks``
  List all tasks grouped by package, with enabled/disabled status.

  .. code-block:: json

     [
       {
         "package": "Pavão",
         "tasks": [
           {
             "id": 1,
             "name": "Refresh secret key",
             "enabled": true
           }
         ]
       }
     ]

``GET /admin/tasks/{task:int}``
  Retrieve task details including schedule and next execution time.

  .. code-block:: json

     {
       "package": "Pavão",
       "name": "Refresh secret key",
       "schedule": "0 0 * * *",
       "enabled": true,
       "running": false,
       "nextExecution": 1729382400
     }

  **404** if task not found.

``POST /admin/tasks/{task:int}/run``
  Trigger immediate execution outside the scheduled window.
  **409** if the task is already running. **404** if not found.

``POST /admin/tasks/{task:int}/stop``
  Cancel a running task execution.
  **409** if the task is not currently running. **404** if not found.

``PUT /admin/tasks/{task:int}/enable``
  Enable a disabled task. Returns the next scheduled execution time.

  .. code-block:: json

     {
       "nextExecution": 1729382400
     }

  **404** if not found.

``DELETE /admin/tasks/{task:int}/enable``
  Disable a task (prevents scheduled and manual execution). **204** on success,
  **404** if not found.

``GET /admin/tasks/{task:int}/output``
  Returns the current execution's output lines as an array of strings, or an empty
  array if the task is not running. **404** if task not found.

``GET /admin/tasks/{task:int}/executions?day=2024-10-18``
  List historical executions for the given day (``YYYY-MM-DD``).

  .. code-block:: json

     [
       {
         "id": 12,
         "success": true,
         "start": 1729296000,
         "finish": 1729296005,
         "outputs": [
           {
             "instant": 1729296001,
             "content": "1 refresh token(s) purged"
           }
         ]
       }
     ]

  **400** if the day format is invalid.

``GET /admin/tasks/{taskId:int}/monitor`` (SSE)
  Server-Sent Events stream of real-time task state changes. The connection stays open
  until the client disconnects; a heartbeat comment is sent every 25 seconds to keep
  the connection alive through proxies.

  .. list-table::
     :header-rows: 1
     :widths: 30 70

     * - Event
       - Meaning
     * - ``taskStart``
       - Task execution began
     * - ``taskEnded``
       - Task execution completed
     * - ``taskOutput``
       - New output line (``data``: line content)
     * - ``taskEnabled``
       - Task enabled/disabled (``data``: ``true`` or ``false``)
     * - ``taskSchedule``
       - Cron schedule changed (``data``: new schedule string)
     * - ``taskDisabled``
       - Task was disabled while running
