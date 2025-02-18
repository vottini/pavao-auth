
import asyncio
import argon2
import hashlib
import pavao

from datetime import datetime
from datetime import timezone

retrieve_password_hash = pavao.include('queries/retrieve_password_hash.sql')
update_password_hash = pavao.include('queries/update_password_hash.sql')

blueprints = pavao.path_to('blueprints.jbp')
internationalization = pavao.Internationalization(
	pavao.path_to('messages')
)

#-------------------------------------------------------------------------------

@pavao.accepts_json(file_blueprint=blueprints, with_root="PasswordUpdate")
async def process(request, response, pg_connection, auth_data, parsed_json):
	localizer = internationalization.create_localizer(
		request.parse_locale_priority())

	if parsed_json.old_password == parsed_json.new_password:
		localizer.assign_response_error(response, "SAME_PASSWORD")
		response.set_status(400)
		return

	try:
		hasher = argon2.PasswordHasher()
		stored_password = await pg_connection.fetchval(
			retrieve_password_hash,
			auth_data.account_id)

		hasher.verify(
			stored_password,
			parsed_json.old_password)

		hashed_password = hasher.hash(parsed_json.new_password)
		await pg_connection.execute(update_password_hash, hashed_password,
			auth_data.account_id)

	except argon2.exceptions.VerifyMismatchError:
		await asyncio.sleep(3)

		response.set_status(400)
		localizer.assign_response_error(response,
			"INVALID_PASSWORD")

#-------------------------------------------------------------------------------

def pavao_endpoint():

	return {
		'method': 'POST',
		'path': '/change-password',
		'processor': process
	}

