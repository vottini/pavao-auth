
import asyncio
import pavao

(pavao.from_module('../common')
	.import_item('assert_admin_access')
	.import_item('create_message_localizer')
	.import_item('localizer'))

retrieve_user = pavao.include("../queries/retrieve_user.sql")
retrieve_user_roles = pavao.include("../queries/retrieve_user_roles.sql")
blueprints = pavao.path_to("../blueprints.jbp")


@pavao.generates_json(file_blueprint=blueprints, with_root="UserRoles")
async def process(request, response, pg_connection, path_variables):
	user_id = path_variables['user']

	user_info = await pg_connection.fetchrow(
		retrieve_user,
		user_id)

	if user_info is None:
		response.set_status(404)
		message_localizer = create_message_localizer(request)
		return message_localizer.create_error("USER_NOT_FOUND")

	roles = await pg_connection.fetch(
		retrieve_user_roles,
		user_id)

	admin = False
	collected_roles = list()

	for role in roles:
		if role['code'] == "PAVAO::ADMIN_ROLE":
			admin = True
			continue

		role_info = pavao.assemble_dicts(role)
		collected_roles.append(role_info)

	result = pavao.assemble_dicts(user_info,
		roles=collected_roles,
		admin=admin)

	return result


@assert_admin_access
def pavao_endpoint():

	return {
		'method': 'GET',
		'path': '/admin/users/{user:int}',
		'package': localizer.map("PACKAGE"),
		'functionality': localizer.map("VIEW_USER"),
		'processor': process
	}

