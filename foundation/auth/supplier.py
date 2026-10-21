
import asyncio
import pavao

pavao.import_module('authorizer')
pavao.import_module('common')
pavao.import_module('jwt')

CURRENT_VERSION = 1
check_schema_version = pavao.include("queries/check_schema_version.sql")

#-------------------------------------------------------------------------------

async def select_data(access_validation):
	has_access, validation_outcome = access_validation
	return validation_outcome if has_access else None


class AuthSupplier(pavao.ParameterSupplier):

	def __init__(self):
		self.token = jwt.JwtSupplier()
		self.authorizer = authorizer.Authorizer(self.token)


	def configure(self, loaded_settings):
		common.process_config(loaded_settings)


	async def initialize(self, pg_connection):
		if not common.enabled:
			return

		try:
			version = await pg_connection.fetchval(check_schema_version)
		except Exception:
			print("pavao-auth: schema version table not found — run 'auth_manager setup' first")
			return

		if version != CURRENT_VERSION:
			print(f"pavao-auth: schema version mismatch (expected {CURRENT_VERSION}, found {version}) — run 'auth_manager migrate'")
			return

		common.schema_ok = True
		await self.authorizer.setup(pg_connection)



	async def validate_access(self, request, endpoint_specs, authorizer):
		return await self.authorizer.validate_access(request,
			endpoint_specs)
	
	
	async def retrieve_authorizer(self): return self.authorizer
	async def retrieve_token(self): return self.token


	def parameters_supplied(self):
		if not common.enabled:
			return dict()

		return {
			'access_validation': [
				self.validate_access,
				None
			],

			'auth_data': [
				select_data,
				None
			],

			'authorizer': [
				self.retrieve_authorizer,
				None
			],

			'token_methods': [
				self.retrieve_token,
				None
			]
		}

