
import re
import asyncio
import pavao

(pavao.from_module('common')
	.import_item('assert_admin_access')
	.import_item('localizer'))

_allowed_pattern = re.compile(r'^[a-z][a-z0-9]*(?:.[a-z0-9]+)?$')
_count_login = "SELECT COUNT(*) FROM pavao.account WHERE login = $1;"


@pavao.generates_json(string_blueprint="root Bool")
@pavao.accepts_parameters({'login': str})
async def process(request, response, parameters, pg_connection):
	if not 'login' in request.params:
		response.set_status(400)
		return

	candidate = parameters['login']
	if _allowed_pattern.search(candidate) is not None:
		count = await pg_connection.fetchval(_count_login, candidate)
		return 0 == count

	return False


@assert_admin_access
def pavao_endpoint():

	return {
		'method': 'GET',
		'path': '/admin/check-login',
		'package': localizer.map("PACKAGE"),
		'functionality': localizer.map("MANAGE_USERS"),
		'processor': process
	}

