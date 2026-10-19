
# pavao-auth

JWT-based authentication and role/permission management extension for
[pavao](https://github.com/vottini/pavao).

## What it provides

**Foundation injectables**

| Name | Type | Description |
|---|---|---|
| `auth_data` | `AuthData` | Decoded token claims for the current request: `account_id`, `token`, `expiration`. `None` if the request is unauthenticated. |
| `access_validation` | `tuple` | Raw `(has_access, outcome)` pair. `outcome` is an `AuthData` on success or an `AuthError` constant on failure. |
| `authorizer` | `Authorizer` | In-memory access control engine. Useful for modules that need to check or modify permissions at runtime. |
| `token_methods` | `JwtSupplier` | JWT generation and validation. Useful for modules that issue tokens (login, refresh). |

**Filter**

`AuthFilter` runs on every non-public endpoint. It validates the `Authorization: Bearer <token>` header, checks the token against the current signing key, and verifies that the caller's roles grant access to the endpoint's declared functionality. It returns:

- `401` — missing, invalid, or expired token; blocked user
- `403` — valid token but insufficient roles
- `410` — endpoint disabled at runtime

**Modules**

- `modules/auth/endpoints/` — login, logout, token refresh, change password, self-info, credentials
- `modules/auth/tasks/` — periodic token blacklist cleanup, token purge, secret key rotation
- `modules/admin/` — full administration API: users, roles, functionalities, task management

## Requirements

- [pavao-postgres](https://github.com/vottini/pavao-postgres) — pavao-auth stores all state in PostgreSQL
- `argon2-cffi` — password hashing (installed automatically from `requirements.txt`)

## Installation

```console
$ pavao-pkg add github.com/vottini/pavao-postgres@<tag>
$ pavao-pkg add github.com/vottini/pavao-auth@<tag>
```

## Configuration

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

Tokens are signed with HMAC-SHA256. The signing key rotates on demand via the
`refresh_skey` scheduled task or by calling `token_methods.refresh_secret_key()`. A
previous key can be kept valid for an overlap period to allow in-flight tokens to finish:

```python
async def process(token_methods):
    token_methods.refresh_secret_key(previous_validity=timedelta(minutes=5))
```

## Documentation

- [Authentication & Authorization](docs/authentication.rst) — setup, auth flows, protecting endpoints, token invalidation, scheduled tasks
- [Administration API](docs/admin.rst) — users, roles, functionalities, task management endpoints
- [JWT](docs/jwt.rst) — token generation, validation, and key rotation

## License

MIT
