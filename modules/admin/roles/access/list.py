
import asyncio
import pavao

(pavao.from_module('../../common')
	.import_item('assert_admin_access')
	.import_item('create_message_localizer')
	.import_item('localizer'))

retrieve_role = pavao.include("../../queries/retrieve_role.sql")
list_role_accesses = pavao.include("../../queries/list_role_accesses.sql")
blueprints = pavao.path_to("../../blueprints.jbp")


@pavao.generates_json(file_blueprint=blueprints, with_root="roleAccesses")
async def process(request, response, pg_connection, path_variables, authorizer):
	role_id = path_variables['role']

	async with pg_connection.transaction():
		role_info = await pg_connection.fetchrow(
			retrieve_role,
			role_id)

		if role_info is None:
			message_localizer = create_message_localizer(request)
			message_localizer.assign_response_error(response, "ROLE_NOT_FOUND")
			response.set_status(404)
			return

		accesses = await pg_connection.fetch(
			list_role_accesses,
			role_id)

	grouped = dict()
	for functionality in accesses:
		package_code = functionality['package']
		package = authorizer.get_package_translation(package_code, request)
		package_funcs = grouped.get(package, list())

		specs = dict(functionality)
		specs["functionality"] = authorizer.get_func_translation(
			package_code, functionality['functionality'],
			request)

		package_funcs.append(specs)
		grouped[package] = package_funcs

	return {
		"name": role_info['name'],
		"accesses": [{'package': package, 'functionalities': funcs}
			for package, funcs in grouped.items()
		]
	}


@assert_admin_access
def pavao_endpoint():

	return {
		'method': 'GET',
		'path': '/admin/roles/{role:int}/accesses',
		'package': localizer.map("PACKAGE"),
		'functionality': localizer.map("LIST_ACCESSES"),
		'processor': process
	}

