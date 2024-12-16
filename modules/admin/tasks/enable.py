
import asyncio
import pavao

(pavao.from_module('../common')
	.import_item('assert_admin_access')
	.import_item('create_message_localizer')
	.import_item('localizer'))

enable_task = pavao.include("../queries/enable_task.sql")
blueprints = pavao.path_to("../blueprints.jbp")

@pavao.generates_json(file_blueprint=blueprints, with_root="updatedSchedule")
async def process(request, response, path_variables, internal_db, server, broadcasting):
	task_data = server.scheduler.get_task(path_variables['task'])

	if task_data is not None:
		await task_data.enable(broadcasting)
		async with internal_db.cursor() as cursor:
			await cursor.execute(enable_task, {
				'task_id': task_data.ident,
				'enabled': True })

		await internal_db.commit()
		return { 'nextExecution': task_data.next_execution }

	else:
		response.set_status(404)
		message_localizer = create_message_localizer(request)
		return message_localizer.create_error(
			"TASK_NOT_FOUND"
		)



@assert_admin_access
def pavao_endpoint():

	return {
		'method': 'PUT',
		'path': '/admin/tasks/{task:int}/enable',
		'package': localizer.map("PACKAGE"),
		'functionality': localizer.map("ENABLE_TASKS"),
		'processor': process
	}

