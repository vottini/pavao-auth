
import asyncio
import pavao

(pavao.from_module('../common.py')
	.import_item('assert_admin_access')
	.import_item('create_message_localizer')
	.import_item('localizer'))

count_admin_accesses = pavao.include(
	"../queries/count_admin_accesses.sql"
)

async def process(request, response, pg_connection, path_variables, authorizer):
	message_localizer = create_message_localizer(request)

	functionality_id = path_variables['functionality']
	admin_roles = await pg_connection.fetchval(count_admin_accesses,
		functionality_id)

	if admin_roles > 0:
		response.set_status(403)
		message_localizer.assign_response_error(response,
			"ADMIN_FUNCTIONALITY")

	else:
		success = await authorizer.disable_functionality(
			pg_connection, functionality_id)

		if not success:
			response.set_status(404)
			message_localizer.assign_response_error(response,
				"FUNCTIONALITY_NOT_FOUND")


@assert_admin_access
def pavao_endpoint():

	return {
		'method': 'PUT',
		'path': '/admin/functionalities/{functionality:int}/disable',
		'package': localizer.map("PACKAGE"),
		'functionality': localizer.map("MANAGE_FUNCTIONALITIES"),
		'processor': process
	}

