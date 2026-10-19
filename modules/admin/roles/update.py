
import asyncio
import asyncpg
import pavao

(pavao.from_module('../common')
	.import_item('assert_admin_access')
	.import_item('create_message_localizer')
	.import_item('localizer'))

update_role = pavao.include("../queries/update_role.sql")
blueprints = pavao.path_to("../blueprints.jbp")


@pavao.accepts_json(file_blueprint=blueprints, with_root="RoleUpdate")
async def process(request, response, parsed_json, pg_connection, path_variables):
	message_localizer = create_message_localizer(request)
	roleId = path_variables['role']
	
	async with pg_connection.transaction():
		for column in ("name", "description"):
			if not pavao.has_optional_field(parsed_json, column):
				continue
			
			try:
				query = update_role.format(column=column)
				column_name = getattr(parsed_json, column)
				updated = await pg_connection.fetchval(query,
					column_name, roleId)
				
				if updated is None:
					response.set_status(404)
					message_localizer.assign_response_error(response,
						"ROLE_NOT_FOUND")
			
			except asyncpg.UniqueViolationError as e:
				response.set_status(409)
				message_localizer.assign_response_error(response,
					"ROLE_EXISTS")


@assert_admin_access
def pavao_endpoint():

	return {
		'method': 'PATCH',
		'path': '/admin/roles/{role:int}',
		'package': localizer.map("PACKAGE"),
		'functionality': localizer.map("MANAGE_ROLES"),
		'processor': process
	}

