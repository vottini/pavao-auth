
import asyncio
import argparse
import readline
import asyncpg
from dataclasses import dataclass
from getpass import getpass
from argon2 import PasswordHasher
import pavao

get_login_count = pavao.include("queries/get_login_count.sql")
insert_user = pavao.include("queries/insert_user.sql")
insert_authentication = pavao.include("queries/insert_authentication.sql")
assign_admin = pavao.include("queries/assign_admin.sql")

#-------------------------------------------------------------------------------

@dataclass
class AdminSpecs:
	first_name: str
	last_name: str
	login: str
	password: str
	change_pw: bool


async def execute(db_settings, admin_specs):

	try:
		db_pool = await asyncpg.create_pool(**db_settings)
		async with db_pool.acquire() as db_connection:
			login_count = await db_connection.fetchval(
				get_login_count, admin_specs.login)

			if login_count > 0:
				print(f"Login '{admin_specs.login}' already exists, aborting...")
				return

	except Exception as e:
		print("Unable to query existing logins: ", e)
		await db_pool.close()
		return

	try:
		async with db_pool.acquire() as db_connection:
			account = await db_connection.fetchval(insert_user, admin_specs.login,
				admin_specs.first_name,
				admin_specs.last_name)

			passwordHash = PasswordHasher().hash(admin_specs.password)
			await db_connection.execute(insert_authentication,
				account, passwordHash, admin_specs.change_pw)

			await db_connection.execute(assign_admin, account)
			print("Success!")

	except Exception as e:
		print("Unable to add login: ", e)

	finally:
		await db_pool.close()

#-------------------------------------------------------------------------------

cli_parser = argparse.ArgumentParser(
	prog="python -m pavao",
	description="Pavão-Auth admin creator")

default_config = "application.yml"
cli_parser.add_argument("--config-file",
	help=f"configuration file to use. Defaults to '{default_config}'",
	action="store", metavar="FILE", required=False, type=str,
	default=default_config)

action_group = cli_parser.add_mutually_exclusive_group(required=True)

action_group.add_argument("--create-admin",
	help="creates an admin account prompting the user for information",
	action="store_true")

action_group.add_argument("--import-admin",
	help="creates an admin account using the given YAML file as specification",
	action="store", metavar="FILE", type=str)

args = cli_parser.parse_args()

database_schema = {
	"host": str,
	"port": 5432,
	"database": str,
	"user": str,
	"password": ""
}

settings = pavao.load_settings(args.config_file, False)
db_settings = settings.get_setting(
	"pavao.database.postgresql",
	database_schema)

#-------------------------------------------------------------------------------

def split(name):
	splitted = name.split(' ')
	not_empty = lambda x : len(x) > 0
	filtered = filter(not_empty, splitted)
	return list(filtered)


def custom_input(prompt, default_text=None):
	if default_text is not None:

		def hook():
			readline.insert_text(default_text)
			readline.redisplay()

		readline.set_pre_input_hook(hook)

	result = ""
	while 0 == len(result):
		result = input(prompt).strip()

	readline.set_pre_input_hook()
	return result


FIRST_NAME = "First name: "
OPTIONAL_LAST_NAME = "Last name (can be left blank): "
CHOOSE_LOGIN = "User login: "
TYPE_PASSWORD = "Password: "
CONFIRM_PASSWORD = "Confirm password: "
CHANGE_PASSWORD_ON_LOGIN = "Change password on next login [Y/n]? "
DEFAULT_CHANGE_PW = "n"

if args.create_admin:
	print("Creating new admin...")

	first_name = custom_input(FIRST_NAME).capitalize()
	last_name = input(OPTIONAL_LAST_NAME).strip().capitalize()
	suggested_login = ".".join(split(first_name) + split(last_name)).lower()
	login = custom_input(CHOOSE_LOGIN, suggested_login)

	password1 = getpass(TYPE_PASSWORD)
	password2 = getpass(CONFIRM_PASSWORD)

	while password1 != password2:
		print("Passwords don't match, try again:")
		password1 = getpass(TYPE_PASSWORD)
		password2 = getpass(CONFIRM_PASSWORD)

	change_pw = custom_input(
		CHANGE_PASSWORD_ON_LOGIN,
		DEFAULT_CHANGE_PW)

	while not change_pw in ['Y', 'n']:
		print("Invalid choice")

		change_pw = custom_input(
			CHANGE_PASSWORD_ON_LOGIN,
			DEFAULT_CHANGE_PW)

	specs = AdminSpecs(first_name,
		last_name if len(last_name) > 0 else None,
		login, password1, change_pw == "Y")

#-------------------------------------------------------------------------------

user_schema = {
	"first_name": str,
	"last_name": "",
	"login": str,
	"password": str,
	"change_password": False
}

def sane_name(name):
	return name.strip().capitalize()

def nullable(name):
	if len(name) == 0: return None
	return name

if (import_file := args.import_admin) is not None:
	loaded_settings = pavao.load_settings(import_file, False)
	admin_settings = loaded_settings.get_setting("admin",
		user_schema)

	specs = AdminSpecs(
		sane_name(admin_settings["first_name"]),
		nullable(sane_name(admin_settings["last_name"])),
		admin_settings["login"].lower(),
		admin_settings["password"],
		admin_settings["change_password"]
	)

#-------------------------------------------------------------------------------

asyncio.run(execute(db_settings, specs))
