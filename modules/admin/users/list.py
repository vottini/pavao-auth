
import asyncio
import pavao

(pavao.from_module('../common')
	.import_item('assert_admin_access')
	.import_item('localizer'))

list_users = pavao.include("../queries/list_users.sql")
blueprints = pavao.path_to("../blueprints.jbp")

@pavao.generates_json(
	file_blueprint=blueprints,
	with_root="userInfo",
	array_root=True)

async def process(auth_data, pg_connection):
	retrieved = await pg_connection.fetch(list_users, auth_data.account_id)
	return [ pavao.assemble_dicts(row) for row in retrieved ]


@assert_admin_access
def pavao_endpoint():

	return {
		'method': 'GET',
		'path': '/admin/users',
		'package': localizer.map("PACKAGE"),
		'functionality': localizer.map("LIST_USERS"),
		'processor': process
	}

