
# pavao-auth

JWT-based authentication and role/permission management extension for
[pavao](https://github.com/vottini/pavao).

## What it provides

**Foundation injectables**

| Name | Type | Description |
|---|---|---|
| `auth_data` | `AuthData` | Decoded token claims for the current request: `account_id`, `token`, `expiration`. `None` if the request is unauthenticated. |

**Filter**

`AuthFilter` runs on every non-public endpoint. It validates the `Authorization: Bearer <token>` header, checks the token against the current signing key, and verifies that the caller's roles grant access to the endpoint's declared functionality. It returns:

- `401` — missing, invalid, or expired token; blocked user
- `403` — valid token but insufficient roles
- `410` — endpoint disabled at runtime

**Auth endpoints**

| Method | Path | Source |
|---|---|---|
| `POST` | `/login` | [login.py](modules/auth/endpoints/login.py) |
| `DELETE` | `/logout` | [logout.py](modules/auth/endpoints/logout.py) |
| `POST` | `/refresh-token` | [refresh_token.py](modules/auth/endpoints/refresh_token.py) |
| `POST` | `/change-password` | [change_password.py](modules/auth/endpoints/change_password.py) |
| `GET` | `/self` | [self.py](modules/auth/endpoints/self.py) |

**Admin endpoints**

| Method | Path | Source |
|---|---|---|
| `GET` | `/admin/check-login` | [check_login.py](modules/admin/check_login.py) |
| `POST` | `/admin/users` | [users/create.py](modules/admin/users/create.py) |
| `GET` | `/admin/users` | [users/list.py](modules/admin/users/list.py) |
| `GET` | `/admin/users/{user}` | [users/retrieve.py](modules/admin/users/retrieve.py) |
| `PATCH` | `/admin/users/{user}` | [users/update.py](modules/admin/users/update.py) |
| `POST` | `/admin/users/{user}/change-password` | [users/change_password.py](modules/admin/users/change_password.py) |
| `PUT` | `/admin/users/{user}/active` | [users/active/enable.py](modules/admin/users/active/enable.py) |
| `DELETE` | `/admin/users/{user}/active` | [users/active/disable.py](modules/admin/users/active/disable.py) |
| `PUT` | `/admin/users/admins` | [users/admins/set.py](modules/admin/users/admins/set.py) |
| `PUT` | `/admin/users/admins/{user}` | [users/admins/include.py](modules/admin/users/admins/include.py) |
| `DELETE` | `/admin/users/admins/{user}` | [users/admins/revoke.py](modules/admin/users/admins/revoke.py) |
| `GET` | `/admin/users/{user}/assignments` | [users/assignments/list.py](modules/admin/users/assignments/list.py) |
| `PUT` | `/admin/users/{user}/assignments` | [users/assignments/set.py](modules/admin/users/assignments/set.py) |
| `POST` | `/admin/roles` | [roles/create.py](modules/admin/roles/create.py) |
| `GET` | `/admin/roles` | [roles/list.py](modules/admin/roles/list.py) |
| `GET` | `/admin/roles/{role}` | [roles/retrieve.py](modules/admin/roles/retrieve.py) |
| `PATCH` | `/admin/roles/{role}` | [roles/update.py](modules/admin/roles/update.py) |
| `DELETE` | `/admin/roles/{role}` | [roles/delete.py](modules/admin/roles/delete.py) |
| `PUT` | `/admin/roles/{role}/assignments` | [roles/assign.py](modules/admin/roles/assign.py) |
| `GET` | `/admin/roles/{role}/accesses` | [roles/access/list.py](modules/admin/roles/access/list.py) |
| `PUT` | `/admin/roles/{role}/access/{functionality}` | [roles/access/create.py](modules/admin/roles/access/create.py) |
| `DELETE` | `/admin/roles/{role}/access/{functionality}` | [roles/access/remove.py](modules/admin/roles/access/remove.py) |
| `GET` | `/admin/functionalities` | [functionalities/list.py](modules/admin/functionalities/list.py) |
| `GET` | `/admin/functionalities/allowed` | [functionalities/allowed.py](modules/admin/functionalities/allowed.py) |
| `PUT` | `/admin/functionalities/{functionality}/enable` | [functionalities/enable.py](modules/admin/functionalities/enable.py) |
| `PUT` | `/admin/functionalities/{functionality}/disable` | [functionalities/disable.py](modules/admin/functionalities/disable.py) |
| `GET` | `/admin/tasks` | [tasks/list.py](modules/admin/tasks/list.py) |
| `GET` | `/admin/tasks/{task}` | [tasks/retrieve.py](modules/admin/tasks/retrieve.py) |
| `POST` | `/admin/tasks/{task}/run` | [tasks/execute.py](modules/admin/tasks/execute.py) |
| `POST` | `/admin/tasks/{task}/stop` | [tasks/stop.py](modules/admin/tasks/stop.py) |
| `PUT` | `/admin/tasks/{task}/enable` | [tasks/enable.py](modules/admin/tasks/enable.py) |
| `DELETE` | `/admin/tasks/{task}/enable` | [tasks/disable.py](modules/admin/tasks/disable.py) |
| `GET` | `/admin/tasks/{task}/executions` | [tasks/executions.py](modules/admin/tasks/executions.py) |
| `GET` | `/admin/tasks/{task}/output` | [tasks/output.py](modules/admin/tasks/output.py) |
| `GET` | `/admin/tasks/{task}/monitor` *(SSE)* | [tasks/monitor.py](modules/admin/tasks/monitor.py) |

**Scheduled tasks**

- [clear_blacklist.py](modules/auth/tasks/clear_blacklist.py) — daily: removes expired entries from the in-memory token blacklist
- [purge_tokens.py](modules/auth/tasks/purge_tokens.py) — hourly: deletes expired refresh tokens from the database
- [refresh_skey.py](modules/auth/tasks/refresh_skey.py) — daily: rotates the JWT signing key (previous key valid for 5 days)

## Requirements

- [pavao-postgres](https://github.com/vottini/pavao-postgres) — pavao-auth stores all state in PostgreSQL
- `argon2-cffi` — password hashing (installed automatically from `requirements.txt`)
- `python-jose[cryptography]` — JWT signing and validation (installed automatically from `requirements.txt`)

## Installation

```console
$ pavao-pkg add github.com/vottini/pavao-postgres@<tag>
$ pavao-pkg add github.com/vottini/pavao-auth@<tag>
```

## Configuration

The filter is **disabled by default** — loading the extension into the foundation
directory does not activate it. Set `pavao.auth.enabled: true` in your configuration
to turn it on.

```yaml
pavao:
  auth:
    enabled: true

  token:
    issuer: myapp.com
    validity:
      access_minutes: 30
      refresh_minutes: 2880   # 48 hours
```

| Key | Default | Description |
|---|---|---|
| `pavao.auth.enabled` | `false` | Enable or disable the extension entirely |
| `pavao.token.issuer` | — | JWT `iss` claim |
| `pavao.token.validity.access_minutes` | — | Access token lifetime |
| `pavao.token.validity.refresh_minutes` | — | Refresh token lifetime |

## First-run setup

Before starting the server, initialize the database schema:

```console
$ python tools/auth/auth_manager.py setup
```

Then create the first administrator account:

```console
$ python tools/auth/auth_manager.py add-admin --interactive
```

On startup, the supplier checks `pavao.schema_version`. If the table is missing
or the version does not match, the filter returns **503** on all protected
endpoints until `auth_manager setup` or `auth_manager migrate` is run.

See [auth_manager tool](docs/create_admin.rst) for the full reference.

## Marking endpoints

By default every endpoint is protected. Use the `public` descriptor key to opt out:

```python
def pavao_endpoint():
    return {
        'method': 'GET',
        'path': '/status',
        'processor': process,
        'public': True,        # no token required
    }
```

To attach fine-grained permission control, add `package` and `functionality` keys. The
filter will verify that the caller's roles include access to that functionality:

```python
def pavao_endpoint():
    return {
        'method': 'DELETE',
        'path': '/users/{id:int}',
        'processor': process,
        'package': 'user_management',
        'functionality': 'delete_user',
    }
```

Both `package` and `functionality` accept plain strings or `LazyLocalizer` objects for
i18n-aware names in admin interfaces.

## JWT implementation

Tokens are signed with HMAC-SHA256. The signing key rotates automatically via the
`refresh_skey` scheduled task. A previous key can be kept valid for an overlap period
to allow in-flight tokens to expire gracefully before the old key is discarded.
See [JWT](docs/jwt.rst) for details.

## Documentation

- [Authentication & Authorization](docs/authentication.rst) — setup, auth flows, protecting endpoints, token invalidation, scheduled tasks
- [Administration API](docs/admin.rst) — users, roles, functionalities, task management endpoints
- [JWT](docs/jwt.rst) — token generation, validation, and key rotation
- [auth_manager tool](docs/create_admin.rst) — database setup and administrator account management

## License

MIT
