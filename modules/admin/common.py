
import os
import functools
import pavao

localization_dir = pavao.path_to("localization")
functionalities_path = os.path.join(localization_dir, 'functionalities')
localizer = pavao.ModuleLocalizer("ADMIN", functionalities_path)
package_mapper = localizer.map("PACKAGE")

messages_path = os.path.join(localization_dir, 'messages')
messages_i18n = pavao.Internationalization(messages_path)

def create_message_localizer(request):
	accepted_languages = request.parse_locale_priority()
	return messages_i18n.create_localizer(accepted_languages)

#------------------------------------------------------------------------------

search_functionality = pavao.include("queries/search_functionality.sql")
insert_functionality = pavao.include("queries/insert_functionality.sql")
insert_admin_access = pavao.include("queries/insert_admin_access.sql")

def assert_admin_access(fnc):

	@functools.wraps(fnc)
	async def wrapped(loaded_settings, stored_settings, pg_connection):

		context = {
			'loaded_settings': loaded_settings,
			'stored_settings': stored_settings,
			'pg_connection': pg_connection,
		}

		adapted_fnc = pavao.async_adapter(pavao.adapter(fnc))
		result = await adapted_fnc(context)
		if not isinstance(result, dict):
			return result

		func_mapper = result.get("functionality")
		if None == func_mapper:
			return result

		async with pg_connection.transaction():
			func_id = await pg_connection.fetchval(search_functionality,
				package_mapper.identity(),
				func_mapper.identity())

			if func_id is None:
				func_id = await pg_connection.fetchval(insert_functionality,
					package_mapper.identity(),
					func_mapper.identity())

			await pg_connection.execute(
				insert_admin_access,
				func_id)

		return result

	return wrapped

#------------------------------------------------------------------------------

def capitalize(text):
	if text is None: return None
	components = [comp.capitalize() for comp in text.strip().split()]
	return " ".join(components)

