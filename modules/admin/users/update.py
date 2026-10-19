
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


@pavao.accepts_json(file_blueprint=blueprints, with_root="UserUpdate")
async def process(request, response, parsed_json, pg_connection, path_variables):
	message_localizer = create_message_localizer(request)
	userId = path_variables['userId']

	async with pg_connection.transaction():
		for column in ("login", "first_name", "last_name"):
			if not pavao.has_optional_field(parsed_json, column):
				continue

			try:
				query = update_user.format(column_name=column)
				await pg_connection.execute(query,
					getattr(parsed_json, column),
					userId)

			except asyncpg.UniqueViolationError as e:
				response.set_status(409)
				message_localizer.assign_response_error(response,
					"LOGIN_EXISTS")


@assert_admin_access
def pavao_endpoint():

	return {
		'method': 'PATCH',
		'path': '/admin/users/{userId:int}',
		'package': localizer.map("PACKAGE"),
		'functionality': localizer.map("MANAGE_USERS"),
		'processor': process
	}

