
import asyncio
import pavao

(pavao.from_module('../common.py')
	.import_item('assert_admin_access')
	.import_item('create_message_localizer')
	.import_item('localizer'))


async def process(request, response, pg_connection, path_variables, authorizer):
	success = await authorizer.enable_functionality(pg_connection,
		path_variables['functionality'])

	if not success:
		response.set_status(404)
		message_localizer = create_message_localizer(request)
		message_localizer.assign_response_error(response,
			"FUNCTIONALITY_NOT_FOUND")


@assert_admin_access
def pavao_endpoint():

	return {
		'method': 'PUT',
		'path': '/admin/functionalities/{functionality:int}/enable',
		'package': localizer.map("PACKAGE"),
		'functionality': localizer.map("MANAGE_FUNCTIONALITIES"),
		'processor': process
	}

