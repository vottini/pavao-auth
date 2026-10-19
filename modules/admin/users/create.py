
import asyncio
import asyncpg
import argon2
import pavao

(pavao.from_module('../common')
	.import_item('assert_admin_access')
	.import_item('create_message_localizer')
	.import_item('capitalize')
	.import_item('localizer'))

add_user = pavao.include("../queries/add_user.sql")
add_authentication = pavao.include("../queries/add_authentication.sql")
blueprints = pavao.path_to("../blueprints.jbp")


@pavao.generates_json(file_blueprint=blueprints, with_root="UserId")
@pavao.accepts_json(file_blueprint=blueprints, with_root="UserCreation")
async def process(request, response, pg_connection, parsed_json):
	hashedPassword = argon2.PasswordHasher().hash(parsed_json.password)
	message_localizer = create_message_localizer(request)

	user_args = (
		parsed_json.login.lower(),
		capitalize(parsed_json.first_name),
		(capitalize(parsed_json.last_name)
			if pavao.has_optional_field(parsed_json, 'last_name')
			else None)
	)

	try:
		async with pg_connection.transaction():
			userId = await pg_connection.fetchval(add_user, *user_args)
			await pg_connection.execute(add_authentication, userId,
				hashedPassword, parsed_json.change_password)

	except asyncpg.UniqueViolationError as e:
		response.set_status(409)
		return message_localizer.create_error("LOGIN_EXISTS")

	response.set_status(201)
	return userId


@assert_admin_access
def pavao_endpoint():

	return {
		'method': 'POST',
		'path': '/admin/users',
		'package': localizer.map("PACKAGE"),
		'functionality': localizer.map("MANAGE_USERS"),
		'processor': process
	}

