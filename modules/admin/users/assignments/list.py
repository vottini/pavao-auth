
import asyncio
import pavao

(pavao.from_module('../../common')
	.import_item('assert_admin_access')
	.import_item('create_message_localizer')
	.import_item('localizer'))

retrieve_user_name = pavao.include("../../queries/retrieve_user_name.sql")
list_assignments = pavao.include("../../queries/list_assignments.sql")
blueprints = pavao.path_to("../../blueprints.jbp")


@pavao.generates_json(file_blueprint=blueprints, with_root="UserAssignments")
async def process(request, response, pg_connection, path_variables):
	target_user = path_variables['user']
	user_data = await pg_connection.fetchrow(
		retrieve_user_name,
		target_user)

	if user_data is None:
		response.set_status(404)
		message_localizer = create_message_localizer(request)
		message_localizer.assign_response_error(
			response, "USER_NOT_FOUND")

	else:
		assignments = await pg_connection.fetch(list_assignments, target_user)
		return pavao.assemble_dicts(user_data, assignments=assignments)


@assert_admin_access
def pavao_endpoint():

	return {
		'method': 'GET',
		'path': '/admin/users/{user:int}/assignments',
		'package': localizer.map("PACKAGE"),
		'functionality': localizer.map("LIST_ASSIGNMENTS"),
		'processor': process
	}

