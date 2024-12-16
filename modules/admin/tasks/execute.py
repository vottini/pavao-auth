
import asyncio
import pavao

(pavao.from_module('../common')
	.import_item('assert_admin_access')
	.import_item('create_message_localizer')
	.import_item('localizer'))

def process(request, response, path_variables, server):
	success, outcome = server.scheduler.run_task(path_variables['task'])
	if success: return

	status, msg = 500, "UNEXPECTED_ERROR"
	if outcome == pavao.TaskProblem.NOT_FOUND:
		msg = "TASK_NOT_FOUND"
		status = 404

	if outcome == pavao.TaskProblem.IN_EXECUTION:
		msg = "TASK_IN_EXECUTION"
		status = 409

	message_localizer = create_message_localizer(request)
	message_localizer.assign_response_error(response, msg)
	response.set_status(status)


@assert_admin_access
def pavao_endpoint():

	return {
		'method': 'POST',
		'path': '/admin/tasks/{task:int}/run',
		'package': localizer.map("PACKAGE"),
		'functionality': localizer.map("RUN_TASKS"),
		'processor': process
	}

