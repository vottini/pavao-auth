
import asyncio
import pavao

(pavao.from_module('../common')
	.import_item('assert_admin_access')
	.import_item('localizer'))

list_roles = pavao.include("../queries/list_roles.sql")
blueprints = pavao.path_to("../blueprints.jbp")


@pavao.generates_json(
	file_blueprint=blueprints,
	with_root="RoleInfo",
	array_root=True)

async def process(pg_connection):
	retrieved = await pg_connection.fetch(list_roles)
	return [ pavao.assemble_dicts(row) for row in retrieved ]


@assert_admin_access
def pavao_endpoint():

	return {
		'method': 'GET',
		'path': '/admin/roles',
		'package': localizer.map("PACKAGE"),
		'functionality': localizer.map("LIST_ROLES"),
		'processor': process
	}

