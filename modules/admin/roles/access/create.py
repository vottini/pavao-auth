
import asyncio
import asyncpg
import pavao

(pavao.from_module('../../common')
	.import_item('assert_admin_access')
	.import_item('create_message_localizer')
	.import_item('localizer'))

insert_role_access = pavao.include("../../queries/insert_role_access.sql")

async def process(request, response, pg_connection, path_variables, authorizer):
	message_localizer = create_message_localizer(request)

	try:
		await pg_connection.execute(insert_role_access,
			path_variables['functionality'],
			path_variables['role'])

		await authorizer.allow_access(pg_connection,
			path_variables['functionality'],
			path_variables['role'])

	except asyncpg.ForeignKeyViolationError:
		message_localizer.assign_response_error(response, "ROLE_NOT_FOUND")
		response.set_status(404)

	except Exception as e:
		pavao.Logger.error(f"Internal error giving role access: {e}")
		message_localizer.assign_response_error(response, "UNEXPECTED_ERROR")
		response.set_status(500)


@assert_admin_access
def pavao_endpoint():

	return {
		'method': 'PUT',
		'path': '/admin/roles/{role:int}/access/{functionality:int}',
		'package': localizer.map("PACKAGE"),
		'functionality': localizer.map("SET_ACCESSES"),
		'processor': process
	}

