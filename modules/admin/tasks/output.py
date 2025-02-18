
import asyncio
import pavao

(pavao.from_module('../common')
	.import_item('assert_admin_access')
	.import_item('create_message_localizer')
	.import_item('localizer'))

blueprints = pavao.path_to("../blueprints.jbp")

@pavao.generates_json(
	file_blueprint=blueprints,
	with_root="String",
	array_root=True)

async def process(request, response, path_variables, server):
	task_data = server.scheduler.get_task(path_variables['task'])

	if task_data is None:
		response.set_status(404)
		message_localizer = create_message_localizer(request)
		return message_localizer.create_error(
			"TASK_NOT_FOUND"
		)

	if task_data.execution is None: return list()
	return task_data.get_output()


@assert_admin_access
def pavao_endpoint():

	return {
		'method': 'GET',
		'path': '/admin/tasks/{task:int}/output',
		'package': localizer.map("PACKAGE"),
		'functionality': localizer.map("MONITOR_TASKS"),
		'processor': process
	}


