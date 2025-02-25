
import os
import functools
import pavao

localization_dir = pavao.path_to("localization")
functionalities_path = os.path.join(localization_dir, 'functionalities')
localizer = pavao.ModuleLocalizer("ADMIN", functionalities_path)
admin_role = 'PAVAO::ADMIN_ROLE'

messages_path = os.path.join(localization_dir, 'messages')
messages_i18n = pavao.Internationalization(messages_path)

def create_message_localizer(request):
	accepted_languages = request.parse_locale_priority()
	return messages_i18n.create_localizer(accepted_languages)

#------------------------------------------------------------------------------

def assert_role_access(pkg_identity, role_code):
	def assert_access(fnc):
		@functools.wraps(fnc)
		async def wrapped(loaded_settings, stored_settings, pg_connection, authorizer):
	
			context = {
				'loaded_settings': loaded_settings,
				'stored_settings': stored_settings,
				'pg_connection': pg_connection
			}
	
			adapted_fnc = pavao.async_adapter(pavao.adapter(fnc))
			result = await adapted_fnc(context)
			if not isinstance(result, dict):
				return result
	
			func_identity = result.get("functionality")
			if None == func_identity:
				return result

			await authorizer.assert_role_access(pg_connection,
				pkg_identity, func_identity,
				role_code) 
	
			return result
	
		return wrapped

	return assert_access

#------------------------------------------------------------------------------

assert_admin_access = assert_role_access(
	localizer.map("PACKAGE"),
	admin_role)

#------------------------------------------------------------------------------

def capitalize(text):
	if text is None: return None
	components = [comp.capitalize() for comp in text.strip().split()]
	return " ".join(components)

