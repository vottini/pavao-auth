
import asyncio
import pavao

(pavao.from_module('../common')
	.import_item('assert_admin_access')
	.import_item('localizer'))

list_functionalities = pavao.include("../queries/list_functionalities.sql")
blueprints = pavao.path_to("../blueprints.jbp")


@pavao.generates_json(
	file_blueprint=blueprints,
	with_root="packageFunctionalities",
	array_root=True)

async def process(request, pg_connection, authorizer):
	functionalities = await pg_connection.fetch(list_functionalities)
	grouped = dict()

	for functionality in functionalities:
		package_code = functionality['package']
		package = authorizer.get_package_translation(package_code, request)
		package_funcs = grouped.get(package, list())

		specs = dict(functionality)
		specs["functionality"] = authorizer.get_func_translation(
			package_code, functionality['functionality'],
			request)

		specs['active'] = True
		package_funcs.append(specs)
		grouped[package] = package_funcs

	return [
		{'package': package, 'functionalities': funcs}
		for package, funcs in grouped.items()
	]


@assert_admin_access
def pavao_endpoint():

	return {
		'method': 'GET',
		'path': '/admin/functionalities',
		'package': localizer.map("PACKAGE"),
		'functionality': localizer.map("LIST_FUNCTIONALITIES"),
		'processor': process
	}

