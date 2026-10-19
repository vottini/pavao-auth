
import secrets

from datetime import datetime, timedelta, timezone
from jose import jwt, exceptions
from pavao import Logger


class SecretKey:
	def __init__(self):
		self.ident = secrets.token_urlsafe(5)
		self.key   = secrets.token_bytes(32)
		self.exp   = None  # set only when placed in past_keys

#-------------------------------------------------------------------------------

class JwtSupplier:
	def __init__(self):
		self.current_key = SecretKey()
		self.past_keys   = dict()


	def refresh_secret_key(self, previous_validity=None):
		if previous_validity is not None:
			if isinstance(previous_validity, int) and previous_validity > 0:
				previous_validity = timedelta(days=previous_validity)

			if not isinstance(previous_validity, timedelta):
				Logger.error(f"Bad argument to refresh_secret_key [{previous_validity}]")
				Logger.error(f"Secret key refresh aborted")
				return False

			if previous_validity.total_seconds() <= 0:
				Logger.error(f"previous_validity must be positive, got {previous_validity}")
				Logger.error(f"Secret key refresh aborted")
				return False

		current_time = datetime.now(tz=timezone.utc)
		previous = self.current_key

		candidate = SecretKey()
		while candidate.ident in self.past_keys:
			candidate = SecretKey()  # pragma: no cover

		filtered = {
			sk.ident: sk
			for sk in self.past_keys.values()
			if sk.exp > current_time
		}

		if previous_validity is not None:
			previous.exp = current_time + previous_validity
			filtered[previous.ident] = previous

		self.past_keys   = filtered
		self.current_key = candidate
		return True


	def generate_token(self, claims):
		return jwt.encode(
			claims,
			self.current_key.key,
			algorithm='HS256',
			headers={'kid': self.current_key.ident}
		)


	def validate_token(self, token):
		try:
			header = jwt.get_unverified_header(token)
		except exceptions.JWTError:
			return None

		if header.get('alg') != 'HS256':
			return None

		generator_ident = header.get('kid')
		if generator_ident is None:
			return None

		current = self.current_key
		generator = (current
			if current.ident == generator_ident
			else self.past_keys.get(generator_ident))

		if generator is None:
			return None

		if generator.exp is not None:
			if generator.exp < datetime.now(tz=timezone.utc):
				return None

		try:
			return jwt.decode(
				token,
				generator.key,
				algorithms=['HS256'],
				options={'verify_aud': False}
			)
		except exceptions.JWTError:
			return None
