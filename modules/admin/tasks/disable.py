
import asyncio
import pavao

(pavao.from_module('../common')
	.import_item('assert_admin_access')
	.import_item('create_message_localizer')
	.import_item('localizer'))

enable_task = pavao.include("../queries/enable_task.sql")

async def process(request, response, path_variables, internal_db, server, broadcasting):
	task_data = server.scheduler.get_task(path_variables['task'])

	if task_data is not None:
		await task_data.disable(broadcasting)
		async with internal_db.cursor() as cursor:
			await cursor.execute(enable_task, {
				'task_id': task_data.ident,
				'enabled': False })

		await internal_db.commit()

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

