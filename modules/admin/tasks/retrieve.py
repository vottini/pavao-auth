
import asyncio
import pavao

(pavao.from_module('../common')
	.import_item('assert_admin_access')
	.import_item('create_message_localizer')
	.import_item('localizer'))

blueprints = pavao.path_to("../blueprints.jbp")

@pavao.generates_json(file_blueprint=blueprints, with_root="TaskInfo")
async def process(request, response, path_variables, server):
	task_data = server.scheduler.get_task(path_variables['task'])
	localization_priority = request.parse_locale_priority()

	if task_data is None:
		response.set_status(404)
		message_localizer = create_message_localizer(request)
		return message_localizer.create_error(
			"TASK_NOT_FOUND"
		)

	result = {
		'name': task_data.localized_name(localization_priority),
		'package': task_data.localized_package(localization_priority),
		'schedule': task_data.schedule,
		'enabled': task_data.enabled,
		'running': task_data.execution is not None
	}

	if task_data.enabled:
		result['nextExecution'] = task_data.next_execution

	return result


@assert_admin_access
async def pavao_endpoint():

	return {
		'method': 'GET',
		'path': '/admin/tasks/{task:int}',
		'package': localizer.map("PACKAGE"),
		'functionality': localizer.map("VIEW_TASK"),
		'processor': process
	}

