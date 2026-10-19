
import asyncio
import pavao

(pavao.from_module('../common')
	.import_item('assert_admin_access')
	.import_item('localizer'))

blueprints = pavao.path_to("../blueprints.jbp")
retrieve_roles_functionalities = pavao.include(
	"../queries/retrieve_roles_functionalities.sql"
)

@pavao.generates_json(
	file_blueprint=blueprints,
	with_root="AllowedFunctionality",
	array_root=True)

@pavao.accepts_parameters({'roles': [int]})
async def process(parameters, response, request, pg_connection, authorizer):
	retrieved = await pg_connection.fetch(
		retrieve_roles_functionalities,
		parameters['roles'])

	translated = [{
		"allowing_role": entry["allowing_role"],
		"package": authorizer.get_package_translation(entry['package'], request),
		"functionality": authorizer.get_func_translation(
			entry['package'], entry['functionality'],
			request)
		}

		for entry in retrieved
	]

	return [
		pavao.assemble_dicts(row)
		for row in translated
	]


@assert_admin_access
def pavao_endpoint():

	return {
		'method': 'GET',
		'path': '/admin/functionalities/allowed',
		'package': localizer.map("PACKAGE"),
		'functionality': localizer.map("LIST_FUNCTIONALITIES"),
		'processor': process
	}

