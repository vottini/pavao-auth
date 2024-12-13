
import asyncio
import pavao

(pavao.from_module('../common')
	.import_item('assert_admin_access')
	.import_item('create_message_localizer')
	.import_item('localizer'))

retrieve_role = pavao.include("../queries/retrieve_role.sql")
retrieve_role_users = pavao.include("../queries/retrieve_role_users.sql")
retrieve_role_accesses = pavao.include("../queries/retrieve_role_accesses.sql")
blueprints = pavao.path_to("../blueprints.jbp")

@pavao.generates_json(file_blueprint=blueprints, with_root="fullRoleData")
async def process(request, response, pg_connection, path_variables, authorizer):
	role_id = path_variables['role']

	async with pg_connection.transaction():
		role_info = await pg_connection.fetchrow(
			retrieve_role, role_id)

		if role_info is None:
			message_localizer = create_message_localizer(request)
			message_localizer.assign_response_error(response, "ROLE_NOT_FOUND")
			response.set_status(404)
			return None

		role_users = await pg_connection.fetch(retrieve_role_users, role_id)
		role_funcs = await pg_connection.fetch(retrieve_role_accesses, role_id)

		translated_role_funcs = list()
		for functionality in role_funcs:
			specs = dict(functionality)

			package_code = functionality['package']
			specs['package'] = authorizer.get_package_translation(package_code, request)
			specs["name"] = authorizer.get_func_translation(package_code,
				specs['name'], request)

			translated_role_funcs.append(specs)

	return pavao.assemble_dicts(role_info,
		functionalities=translated_role_funcs,
		users=role_users)


@assert_admin_access
def pavao_endpoint():

	return {
		'method': 'GET',
		'path': '/admin/roles/{role:int}',
		'package': localizer.map("PACKAGE"),
		'functionality': localizer.map("VIEW_ROLE"),
		'processor': process
	}

