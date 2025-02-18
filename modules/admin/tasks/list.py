
import asyncio
import pavao

(pavao.from_module('../common')
	.import_item('assert_admin_access')
	.import_item('localizer'))

blueprints = pavao.path_to("../blueprints.jbp")


@pavao.generates_json(
	file_blueprint=blueprints,
	with_root="PackageTasks",
	array_root=True)

async def process(server, request):
	localization_priority = request.parse_locale_priority()
	grouped = dict()

	for task in server.scheduler.list_tasks(localization_priority):
		package = task['package']
		package_funcs = grouped.get(package, list())
		package_funcs.append(dict(task))
		grouped[package] = package_funcs

	return [
		{ 'package': package, 'tasks': tasks }
		for package, tasks in grouped.items()
	]


@assert_admin_access
def pavao_endpoint():

	return {
		'method': 'GET',
		'path': '/admin/tasks',
		'package': localizer.map("PACKAGE"),
		'functionality': localizer.map("LIST_TASKS"),
		'processor': process
	}

