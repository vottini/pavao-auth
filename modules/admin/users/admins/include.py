
import asyncio
import pavao

(pavao.from_module('../../common')
	.import_item('assert_admin_access')
	.import_item('localizer'))


add_admin = pavao.include("../../queries/add_admin.sql")

async def process(request, response, pg_connection, path_variables):
	await pg_connection.execute(add_admin, path_variables['user'])
	response.set_status(204)


@assert_admin_access
def pavao_endpoint():

	return {
		'method': 'PUT',
		'path': '/admin/users/admins/{user:int}',
		'package': localizer.map("PACKAGE"),
		'functionality': localizer.map("MODIFY_ADMIN"),
		'processor': process
	}

