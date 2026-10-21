
import asyncio
import pavao

pavao.import_module('common')
pavao.import_module('authorizer', with_name='auth')

class AuthFilter(pavao.RequestFilter):
	async def init(self, loaded_settings):
		common.process_config(loaded_settings)


	async def enabled(self, endpoint_specs, authorizer, pg_connection):
		if not common.enabled: return False
		if endpoint_specs.get('public') is True: return False
		if not common.schema_ok: return True

		await authorizer.register_functionality(
			endpoint_specs,
			pg_connection)

		return True


	async def allow(self, access_validation, response):
		if not common.schema_ok:
			response.set_status(503)
			return False

		has_access, validation_outcome = access_validation
		if has_access: return True

		if validation_outcome in (
			auth.AuthError.MISSING_TOKEN,
			auth.AuthError.INVALID_TOKEN,
			auth.AuthError.EXPIRED_AUTH,
			auth.AuthError.BLOCKED_USER
		): status = 401
		elif validation_outcome is auth.AuthError.NOT_ALLOWED: status = 403
		elif validation_outcome is auth.AuthError.DISABLED_ENDPOINT: status = 410
		else: status = 500
		response.set_status(status)
		return False
