
import asyncio
import pavao

(pavao.from_module('../../common')
	.import_item('assert_admin_access')
	.import_item('localizer'))

get_admin = pavao.include("../../queries/get_admin.sql")
insert_admins = pavao.include("../../queries/insert_admins.sql")
remove_admins = pavao.include("../../queries/remove_admins.sql")
blueprints = pavao.path_to("../../blueprints.jbp")


@pavao.accepts_json(
	file_blueprint=blueprints,
	with_root="userId",
	array_root=True)

async def process(request, response, parsed_json, pg_connection, auth_data):
	parsed_json.append(auth_data.account_id)

	async with pg_connection.transaction():
		admin_id = await pg_connection.fetchval(get_admin)
		await pg_connection.execute(insert_admins, admin_id, parsed_json)
		await pg_connection.execute(remove_admins, admin_id, parsed_json)


@assert_admin_access
def pavao_endpoint():

	return {
		'method': 'PUT',
		'path': '/admin/users/admins',
		'package': localizer.map("PACKAGE"),
		'functionality': localizer.map("MODIFY_ADMIN"),
		'processor': process
	}

