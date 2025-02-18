
import asyncio
import asyncpg
import pavao

(pavao.from_module('../common')
	.import_item('assert_admin_access')
	.import_item('create_message_localizer')
	.import_item('capitalize')
	.import_item('localizer'))

add_role = pavao.include("../queries/add_role.sql")
blueprints = pavao.path_to("../blueprints.jbp")

@pavao.generates_json(file_blueprint=blueprints, with_root="RoleId")
@pavao.accepts_json(file_blueprint=blueprints, with_root="RoleCreation")
async def process(request, response, parsed_json, pg_connection):
	message_localizer = create_message_localizer(request)

	description = (parsed_json.description.strip()
		if pavao.has_optional_field(parsed_json, 'description')
		else None)

	try:
		roleId = await pg_connection.fetchval(add_role,
			capitalize(parsed_json.name),
			description)

	except asyncpg.UniqueViolationError as e:
		response.set_status(409)
		return message_localizer.create_error(
			"ROLE_EXISTS"
		)

	response.set_status(201)
	return roleId


@assert_admin_access
def pavao_endpoint():

	return {
		'method': 'POST',
		'path': '/admin/roles',
		'package': localizer.map("PACKAGE"),
		'functionality': localizer.map("CREATE_ROLES"),
		'processor': process
	}

