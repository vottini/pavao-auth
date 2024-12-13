
import asyncio
import pavao

(pavao.from_module('../../common')
	.import_item('assert_admin_access')
	.import_item('create_message_localizer')
	.import_item('localizer'))

remove_admin = pavao.include("../../queries/remove_admin.sql")

async def process(request, response, pg_connection, path_variables, auth_data):
	message_localizer = create_message_localizer(request)
	revoked_user = path_variables['user']

	if auth_data.account_id == revoked_user:
		message_localizer.assign_response_error(response, "REVOKE_OWN_USER")
		response.set_status(403)
		return

	revoked = await pg_connection.fetch(
		remove_admin, revoked_user)

	if len(revoked) == 0:
		message_localizer.assign_response_error(response, "USER_NOT_FOUND")
		response.set_status(404)


@assert_admin_access
def pavao_endpoint():

	return {
		'method': 'DELETE',
		'path': '/admin/users/admins/{user:int}',
		'package': localizer.map("PACKAGE"),
		'functionality': localizer.map("MODIFY_ADMIN"),
		'processor': process
	}

