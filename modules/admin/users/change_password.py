
import asyncio
import asyncpg
import argon2
import pavao

(pavao.from_module('../common')
	.import_item('assert_admin_access')
	.import_item('create_message_localizer')
	.import_item('localizer'))

update_authentication = pavao.include("../queries/update_authentication.sql")
blueprints = pavao.path_to("../blueprints.jbp")

@pavao.accepts_json(file_blueprint=blueprints, with_root="passwordUpdate")
async def process(request, response, pg_connection, parsed_json, path_variables):
	localizer = create_message_localizer(request)

	user_id = path_variables['user']
	hashed_password = argon2.PasswordHasher().hash(parsed_json.password)
	change_afterwards = (pavao.has_optional_field(parsed_json, 'change_password')
		and parsed_json.change_password)

	try:
		found_account = await pg_connection.fetchval(update_authentication,
			user_id, hashed_password, change_afterwards)

		if found_account is None:
			localizer.assign_response_error(response, "USER_NOT_FOUND")
			response.set_status(404)
			return

	except asyncpg.PostgresError as e:
		pavao.Logger.error(f"Error changing password: {e}")
		localizer.assign_response_error(response, "UNEXPECTED_ERROR")
		response.set_status(500)


@assert_admin_access
def pavao_endpoint():

	return {
		'method': 'POST',
		'path': '/admin/users/{user:int}/change-password',
		'package': localizer.map("PACKAGE"),
		'functionality': localizer.map("EDIT_USERS"),
		'processor': process
	}

