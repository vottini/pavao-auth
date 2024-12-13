
import asyncio
import pavao

(pavao.from_module('../../common')
	.import_item('assert_admin_access')
	.import_item('create_message_localizer')
	.import_item('localizer'))

enable_user = pavao.include("../../queries/enable_user.sql")

async def process(request, response, pg_connection, path_variables):
	message_localizer = create_message_localizer(request)
	enabled = await pg_connection.fetchval(enable_user,
		path_variables['user'], True)

	if enabled is None:
		message_localizer.assign_response_error(response, "USER_NOT_FOUND")
		response.set_status(404)


@assert_admin_access
def pavao_endpoint():

	return {
		'method': 'PUT',
		'path': '/admin/users/{user:int}/active',
		'package': localizer.map("PACKAGE"),
		'functionality': localizer.map("EDIT_USERS"),
		'processor': process
	}

