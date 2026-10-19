
import re
import datetime
import asyncio
import pavao

(pavao.from_module('../common')
	.import_item('assert_admin_access')
	.import_item('create_message_localizer')
	.import_item('localizer'))

day_pattern = re.compile(r"^[0-9]{4}-[0-9]{2}-[0-9]{2}$")
blueprints = pavao.path_to("../blueprints.jbp")

#-------------------------------------------------------------------------------

@pavao.generates_json(
	file_blueprint=blueprints,
	with_root="TaskExecution",
	array_root=True)

@pavao.accepts_parameters({'day': str})
async def process(request, response, parameters, task_store, path_variables):
	day = parameters['day']

	if day_pattern.match(day) is None:
		response.set_status(400)
		message_localizer = create_message_localizer(request)
		return message_localizer.create_error(
			"INVALID_DAY"
		)

	parsed_day = datetime.date.fromisoformat(day)
	found = await task_store.get_executions(path_variables['task'], parsed_day)

	outputs = dict()
	for execution in found:
		ident = execution['id']
		outputs[ident] = await task_store.get_outputs(ident)

	return [
		pavao.assemble_dicts(execution, outputs=[
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


