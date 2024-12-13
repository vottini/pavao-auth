
import asyncio
import asyncpg
import pavao

(pavao.from_module('../../common')
	.import_item('assert_admin_access')
	.import_item('create_message_localizer')
	.import_item('localizer'))

assign_roles = pavao.include("../../queries/assign_roles.sql")
revoke_roles = pavao.include("../../queries/revoke_roles.sql")
blueprints = pavao.path_to("../../blueprints.jbp")


@pavao.accepts_json(
	file_blueprint=blueprints,
	with_root="roleId",
	array_root=True)

async def process(authorizer, request, response, parsed_json, path_variables, pg_connection):
	message_localizer = create_message_localizer(request)
	user_id = path_variables['user']
	roles = parsed_json

	try:
		async with pg_connection.transaction():
			await pg_connection.execute(assign_roles, roles, user_id)
			await pg_connection.execute(revoke_roles, roles, user_id)

		authorizer.mark_modified(user_id)

	except asyncpg.ForeignKeyViolationError:
		message_localizer.assign_response_error(response, "USER_NOT_FOUND")
		response.set_status(404)

	except Exception as e:
		pavao.Logger.error(f"Internal error assigning user: {e}")
		message_localizer.assign_response_error(response, "UNEXPECTED_ERROR")
		response.set_status(500)


@assert_admin_access
def pavao_endpoint():

	return {
		'method': 'PUT',
		'path': '/admin/users/{user:int}/assignments',
		'package': localizer.map("PACKAGE"),
		'functionality': localizer.map("SET_ASSIGNMENTS"),
		'processor': process
	}

