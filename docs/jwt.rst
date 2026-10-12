
JWT
***

``JwtSupplier`` is a self-contained utility class that handles token generation,
validation, and signing-key rotation. Instantiate it wherever your authentication
logic lives — typically inside the auth supplier:

.. code-block:: python

   from auth.jwt import JwtSupplier

   class AuthSupplier(pavao.ParameterSupplier):
     def __init__(self):
       self.jwt = JwtSupplier()

A single ``JwtSupplier`` instance should be shared across all modules that need to
issue or validate tokens, since all tokens must be verified against the same signing
keys. Holding it in a supplier ensures the instance is created once and is available
wherever it is needed.

Generating tokens
=================

.. code-block:: python

   from datetime import datetime, timezone, timedelta

   now = datetime.now(timezone.utc)
   claims = {
     'sub': user_id,
     'iat': now.timestamp(),
     'exp': (now + timedelta(minutes=30)).timestamp()
   }

   token = self.jwt.generate_token(claims)

``claims`` is a plain dict. Any JSON-serializable values are accepted; the standard
fields (``sub``, ``iat``, ``exp``) are not enforced — the application is responsible
for including and interpreting them. ``generate_token`` returns a signed HS256 JWT
string.

Validating tokens
=================

.. code-block:: python

   claims = self.jwt.validate_token(token_string)
   if claims is None:
     # malformed, unknown key, or expired key
     ...

``validate_token`` returns the claims dict if the token is structurally valid and its
signature matches a known key, or ``None`` if it is malformed, signed with an unknown
key, or was issued with a key that has since expired. The application is responsible for
checking ``exp`` and other application-level claims after a successful validation.

Key rotation
============

Signing keys are generated automatically when ``JwtSupplier`` is instantiated. To rotate
to a new key:

.. code-block:: python

   self.jwt.refresh_secret_key()

Tokens signed with the old key are immediately invalidated. To keep old tokens valid
during a transition window:

.. code-block:: python

   self.jwt.refresh_secret_key(previous_validity=7)      # keep old key valid for 7 days
   self.jwt.refresh_secret_key(previous_validity=timedelta(hours=2))

``previous_validity`` accepts either a positive integer (days) or a ``timedelta``.
Multiple past keys can be active simultaneously; each is tracked by its identifier
embedded in the token.

Token configuration
===================

The following keys in ``application.yml`` are available for applications that choose to
honour them (``JwtSupplier`` does not read them automatically — they are intended for use
in the supplier's ``configure`` method):

.. list-table::
   :header-rows: 1
   :widths: 45 55

   * - Key
     - Description
   * - ``pavao.token.issuer``
     - Issuer string to embed in token claims
   * - ``pavao.token.validity.access_minutes``
     - Access token lifetime in minutes
   * - ``pavao.token.validity.refresh_minutes``
     - Refresh token lifetime in minutes
