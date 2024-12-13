
import asyncio
import pavao

(pavao.from_module('../common')
	.import_item('assert_admin_access')
	.import_item('create_message_localizer')
	.import_item('localizer'))

remove_role = pavao.include("../queries/remove_role.sql")

async def process(request, response, pg_connection, path_variables):
	message_localizer = create_message_localizer(request)

	try:
		deleted = await pg_connection.fetchval(remove_role,
			path_variables['roleId'])

		if deleted is None:
			message_localizer.assign_response_error(response, "ROLE_NOT_FOUND")
			response.set_status(404)

	except Exception as e:
		pavao.Logger.error(f"Internal error removing role: {e}")
		message_localizer.assign_response_error(response, "UNEXPECTED_ERROR")
		response.set_status(500)


@assert_admin_access
def pavao_endpoint():

	return {
		'method': 'DELETE',
		'path': '/admin/roles/{roleId:int}',
		'package': localizer.map("PACKAGE"),
		'functionality': localizer.map("CREATE_ROLES"),
		'processor': process
	}

