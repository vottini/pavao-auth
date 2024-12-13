
import asyncio
import asyncpg
import pavao

(pavao.from_module('../../common')
	.import_item('assert_admin_access')
	.import_item('create_message_localizer')
	.import_item('localizer'))

assign_role_users = pavao.include("../../queries/assign_role_users.sql")
revoke_role_users = pavao.include("../../queries/revoke_role_users.sql")
blueprints = pavao.path_to("../../blueprints.jbp")


@pavao.accepts_json(
	file_blueprint=blueprints,
	with_root="userId",
	array_root=True)

async def process(request, response, parsed_json, path_variables, pg_connection):
	role_id = path_variables['role']
	users = parsed_json

	try:
		async with pg_connection.transaction():
			await pg_connection.execute(assign_role_users, users, role_id)
			await pg_connection.execute(revoke_role_users, users, role_id)

	except asyncpg.ForeignKeyViolationError:
		message_localizer = create_message_localizer(request)
		localizer.assign_response_error(response, "ROLE_NOT_FOUND")
		response.set_status(404)


@assert_admin_access
def pavao_endpoint():

	return {
		'method': 'PUT',
		'path': '/admin/roles/{role:int}/assignments',
		'package': localizer.map("PACKAGE"),
		'functionality': localizer.map("SET_ASSIGNMENTS"),
		'processor': process
	}

