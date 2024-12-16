
import re
import datetime
import asyncio
import pavao

(pavao.from_module('../common')
	.import_item('assert_admin_access')
	.import_item('create_message_localizer')
	.import_item('localizer'))

day_pattern = re.compile(r"^[0-9]{4}-[0-9]{2}-[0-9]{2}$")
list_task_executions = pavao.include("../queries/list_task_executions.sql")
retrieve_task_output = pavao.include("../queries/retrieve_task_output.sql")
blueprints = pavao.path_to("../blueprints.jbp")

#-------------------------------------------------------------------------------

def map_execution(row):
	return {
		'id': row[0],
		'success': row[1],
		'start': row[2],
		'finish': row[3]
	}

def map_output(row):
	return {
		'instant': row[0],
		'content': row[1]
	}

#-------------------------------------------------------------------------------

@pavao.generates_json(
	file_blueprint=blueprints,
	with_root="taskExecution",
	array_root=True)

@pavao.accepts_parameters({'day': str})
async def process(request, response, parameters, internal_db, path_variables):
	day = parameters['day']

	if day_pattern.match(day) is None:
		response.set_status(400)
		message_localizer = create_message_localizer(request)
		return message_localizer.create_error(
			"INVALID_DAY"
		)

	async with internal_db.execute(
		list_task_executions, {
			'task': path_variables['task'],
			'start': day
		}) as cursor:

		found = [ map_execution(row)
			for row in await cursor.fetchall()
		]

	outputs = dict()
	for execution in found:
		ident = execution['id']

		async with internal_db.execute(
			retrieve_task_output,
			[ident]) as cursor:

			outputs[ident] = [ map_output(row)
				for row in await cursor.fetchall()
			]

	return [
		pavao.assemble_dicts(execution,
			outputs=[
				pavao.assemble_dicts(output)
				for output in outputs.get(execution['id'], list())
			])

		for execution in found
	]


@assert_admin_access
def pavao_endpoint():

	return {
		'method': 'GET',
		'path': '/admin/tasks/{task:int}/executions',
		'package': localizer.map("PACKAGE"),
		'functionality': localizer.map("MONITOR_TASKS"),
		'processor': process,
		'public': True
	}


