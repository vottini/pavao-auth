
import asyncio
import argon2
import hashlib
import pavao

from datetime import datetime
from datetime import timezone

retrieve_password_hash = pavao.include('queries/retrieve_password_hash.sql')
update_password_hash = pavao.include('queries/update_password_hash.sql')

pavao.import_module("credentials")
blueprints = pavao.path_to('blueprints.jbp')
internationalization = pavao.Internationalization(
	pavao.path_to('messages')
)

#-------------------------------------------------------------------------------

@pavao.accepts_json(file_blueprint=blueprints, with_root="passwordUpdate")
async def process(request, response, pg_connection, auth_data, parsed_json):
	localizer = internationalization.create_localizer(
		request.parse_locale_priority())

	if parsed_json.old_password == parsed_json.new_password:
		response.set_status(400)
		localizer.assign_response_error(response,
			"SAME_PASSWORD")

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

	except Exception as e:
		msg = f"Error updating password: {e}"
		pavao.Logger.error(msg)

		response.set_status(500)
		localizer.assign_response_error(response,
			"INTERNAL_ERROR")

#-------------------------------------------------------------------------------

def pavao_endpoint():

	return {
		'method': 'POST',
		'path': '/change-password',
		'processor': process
	}

