
import asyncio
import pavao

(pavao.from_module('../common.py')
	.import_item('assert_admin_access')
	.import_item('localizer'))

list_users = pavao.include("../queries/list_users.sql")
count_admin_roles = pavao.include('../queries/count_admin_roles.sql')
blueprints = pavao.path_to("../blueprints.jbp")

async def is_admin(pg_connection, user_data):
	user_id = user_data['id']

	admin_roles = await pg_connection.fetchval(
		count_admin_roles,
		user_id)

	return admin_roles > 0


@pavao.generates_json(
	file_blueprint=blueprints,
	with_root="UserInfo",
	array_root=True)

async def process(auth_data, pg_connection):
	users = await pg_connection.fetch(list_users,
		auth_data.account_id)

	return [
		pavao.assemble_dicts(row,
			admin=(await is_admin(pg_connection, row))
		)

		for row in users
	]


@assert_admin_access
def pavao_endpoint():

	return {
		'method': 'GET',
		'path': '/admin/users',
		'package': localizer.map("PACKAGE"),
		'functionality': localizer.map("LIST_USERS"),
		'processor': process
	}

