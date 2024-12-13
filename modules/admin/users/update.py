
import asyncio
import asyncpg
import humps
import pavao

(pavao.from_module('../common')
	.import_item('assert_admin_access')
	.import_item('create_message_localizer')
	.import_item('localizer'))

update_user = pavao.include("../queries/update_user.sql")
blueprints = pavao.path_to("../blueprints.jbp")

@pavao.accepts_json(file_blueprint=blueprints, with_root="userUpdate")
async def process(request, response, parsed_json, pg_connection, path_variables):
	message_localizer = create_message_localizer(request)
	userId = path_variables['userId']

	async with pg_connection.transaction():
		for column in ("login", "firstName", "lastName"):
			if not pavao.has_optional_field(parsed_json, column):
				continue

			snake_case_column = humps.decamelize(column)
			query = update_user.format(column_name=snake_case_column)

			try:
				await pg_connection.execute(query,
					getattr(parsed_json, column),
					userId)

			except asyncpg.UniqueViolationError as e:
				message_localizer.assign_response_error(response, "LOGIN_EXISTS")
				response.set_status(409)
				return

			except asyncpg.PostgresError as e:
				pavao.Logger.error(f"Internal error updating role: {e}")
				message_localizer.assign_response_error(response, "UNEXPECTED_ERROR")
				response.set_status(500)
				return


@assert_admin_access
def pavao_endpoint():

	return {
		'method': 'PATCH',
		'path': '/admin/users/{userId:int}',
		'package': localizer.map("PACKAGE"),
		'functionality': localizer.map("EDIT_USERS"),
		'processor': process
	}

