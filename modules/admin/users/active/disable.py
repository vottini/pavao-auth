
import asyncio
import pavao

(pavao.from_module('../../common')
	.import_item('assert_admin_access')
	.import_item('create_message_localizer')
	.import_item('localizer'))

enable_user = pavao.include("../../queries/enable_user.sql")

async def process(request, response, pg_connection, path_variables, auth_data):
	message_localizer = create_message_localizer(request)
	target_user = path_variables['user']

	if auth_data.account_id == target_user:
		message_localizer.assign_response_error(response, "DISABLE_OWN_USER")
		response.set_status(403)
		return

	disabled = await pg_connection.execute(
		enable_user, target_user, False)

	if len(disabled) == 0:
		message_localizer.assign_response_error(response, "USER_NOT_FOUND")
		response.set_status(404)


@assert_admin_access
def pavao_endpoint():

	return {
		'method': 'DELETE',
		'path': '/admin/users/{user:int}/active',
		'package': localizer.map("PACKAGE"),
		'functionality': localizer.map("EDIT_USERS"),
		'processor': process
	}

