
import asyncio
import hashlib
import pavao

from datetime import datetime
from datetime import timezone

find_refresh = pavao.include('queries/find_refresh.sql')
select_roles_for_user = pavao.include('queries/select_roles_for_user.sql')
select_whether_active = pavao.include('queries/select_whether_active.sql')
remove_refresh = pavao.include('queries/remove_refresh.sql')
insert_refresh = pavao.include('queries/insert_refresh.sql')

pavao.import_module("credentials")
blueprints = pavao.path_to('blueprints.jbp')
internationalization = pavao.Internationalization(
	pavao.path_to('messages')
)

#-------------------------------------------------------------------------------

@pavao.generates_json(file_blueprint=blueprints, with_root="TokenInfo")
async def process(request, response, pg_connection, token_methods):
	accepted_languages = request.parse_locale_priority()
	localizer = internationalization.create_localizer(accepted_languages)
	token = request.cookies.get('token')

	if token is None:
		response.set_status(400)
		return localizer.create_error(
			"MISSING_TOKEN"
		)

	refresh_claims = token_methods.validate_token(token)

	if refresh_claims is None:
		response.set_status(400)
		return localizer.create_error(
			"INVALID_TOKEN"
		)

	account_id = refresh_claims['sub']
	is_active = await pg_connection.fetchval(
		select_whether_active,
		account_id)

	if not is_active:
		response.set_status(401)
		return localizer.create_error(
			"DISABLED_USER"
		)

	refresh_hash = hashlib.md5(
		refresh_claims['jti'].encode()
	).digest().hex()

	found_refresh = await pg_connection.fetchrow(
		find_refresh, account_id,
		refresh_hash)

	if found_refresh is None:
		response.set_status(400)
		return localizer.create_error(
			"INVALID_TOKEN"
		)

	now = datetime.now(timezone.utc)
	if found_refresh['expiration'] < now:
		response.set_status(400)
		return localizer.create_error(
			"INVALID_TOKEN"
		)

	access_claims = credentials.create_claims(account_id, now,
		credentials.access_validity)

	roles = await pg_connection.fetch(
		select_roles_for_user,
		account_id)

	roles_ids = [ str(role['id']) for role in roles ]
	access_claims['roles'] = ",".join(roles_ids)
	refresh_claims = credentials.create_claims(account_id, now,
		credentials.refresh_validity)

	refresh_hash = hashlib.md5(refresh_claims['jti'].encode()).digest().hex()
	refresh_expiry = datetime.utcfromtimestamp(refresh_claims['exp'])

	async with pg_connection.transaction():
		await pg_connection.execute(remove_refresh, found_refresh['id'])
		await pg_connection.execute(insert_refresh, account_id, refresh_hash,
			refresh_expiry, access_claims['jti'])

	access_token = token_methods.generate_token(access_claims)
	refresh_token = token_methods.generate_token(refresh_claims)

	response.add_cookie(
		pavao.http.Cookie('token', refresh_token)
			.set_sameSite(pavao.http.SameSite.STRICT)
			.set_path('/refresh-token')
			.set_httpOnly()
	)

	return {
		"token": access_token,
		"changePassword": False,
		"expires": access_claims['exp']
	}

#-------------------------------------------------------------------------------

def pavao_endpoint():

	return {
		'method': 'GET',
		'path': '/refresh-token',
		'processor': process,
		'public': True
	}

