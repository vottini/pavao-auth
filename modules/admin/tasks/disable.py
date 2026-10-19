
import asyncio
import pavao

(pavao.from_module('../common')
	.import_item('assert_admin_access')
	.import_item('create_message_localizer')
	.import_item('localizer'))

async def process(request, response, path_variables, task_store, server, broadcasting):
	task_data = server.scheduler.get_task(path_variables['task'])

	if task_data is not None:
		await task_data.disable(broadcasting)
		await task_store.set_task_enabled(task_data.ident, False)

	else:
		message_localizer = create_message_localizer(request)
		message_localizer.assign_response_error(response, "TASK_NOT_FOUND")
		response.set_status(404)


@assert_admin_access
def pavao_endpoint():

	return {
		'method': 'DELETE',
		'path': '/admin/tasks/{task:int}/enable',
		'package': localizer.map("PACKAGE"),
		'functionality': localizer.map("ENABLE_TASKS"),
		'processor': process
	}

