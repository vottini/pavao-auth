
import os
import asyncio
import pavao

pavao.import_module('authorizer')
pavao.import_module('common')

queries_dir = pavao.path_to("database")
db_creation = [arq for arq in os.listdir(queries_dir) if arq.endswith('.sql')]
db_creation.sort()

#-------------------------------------------------------------------------------

async def select_data(access_validation):
	has_access, validation_outcome = access_validation
	return validation_outcome if has_access else None


class AuthSupplier(pavao.ParameterSupplier):

	def __init__(self):
		self.token = pavao.JwtSupplier()
		self.authorizer = authorizer.Authorizer(self.token)


	def configure(self, loaded_settings):
		common.process_config(loaded_settings)


	async def initialize(self, pg_connection):
		if not common.enabled:
			return

		for query in db_creation:
			with open(os.path.join(queries_dir, query)) as fd:
				await pg_connection.execute(fd.read())

		await self.authorizer.assert_role_existence(pg_connection,
			"PAVAO::ADMIN_ROLE", "Administrator",
			None)



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

