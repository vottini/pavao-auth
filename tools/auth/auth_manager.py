
import asyncio
import argparse
import readline
import asyncpg
from dataclasses import dataclass
from getpass import getpass
from pathlib import Path
from argon2 import PasswordHasher
import pavao

CURRENT_VERSION = 1

HERE = Path(__file__).parent
FOUNDATION = HERE.parent.parent / "foundation" / "auth"
DB_SCRIPTS_DIR = HERE / "database"
QUERIES_DIR = HERE / "queries"

def _sql(path):
    with open(path) as f:
        return f.read()

get_login_count      = _sql(QUERIES_DIR / "get_login_count.sql")
insert_user          = _sql(QUERIES_DIR / "insert_user.sql")
insert_authentication = _sql(QUERIES_DIR / "insert_authentication.sql")
assign_admin         = _sql(QUERIES_DIR / "assign_admin.sql")
assert_role_exists   = _sql(FOUNDATION / "queries" / "assert_role_exists.sql")

#-------------------------------------------------------------------------------

@dataclass
class AdminSpecs:
	first_name: str
	last_name: str
	login: str
	password: str
	change_pw: bool

#-------------------------------------------------------------------------------

async def cmd_setup(db_settings):
	try:
		db_pool = await asyncpg.create_pool(**db_settings)
	except Exception as e:
		print("Unable to connect to database:", e)
		return

	try:
		async with db_pool.acquire() as conn:
			for script in sorted(DB_SCRIPTS_DIR.glob("*.sql")):
				await conn.execute(script.read_text())

			await conn.fetchval(assert_role_exists,
				"PAVAO::ADMIN_ROLE", "Administrator", None)

			await conn.execute(
				"INSERT INTO pavao.schema_version (version) VALUES ($1)",
				CURRENT_VERSION)

		print("Setup complete.")

	except Exception as e:
		print("Setup failed:", e)

	finally:
		await db_pool.close()


async def cmd_add_admin(db_settings, specs):
	try:
		db_pool = await asyncpg.create_pool(**db_settings)
		async with db_pool.acquire() as conn:
			login_count = await conn.fetchval(get_login_count, specs.login)
			if login_count > 0:
				print(f"Login '{specs.login}' already exists, aborting...")
				await db_pool.close()
				return

	except Exception as e:
		print("Unable to query existing logins:", e)
		await db_pool.close()
		return

	try:
		async with db_pool.acquire() as conn:
			account = await conn.fetchval(insert_user,
				specs.login, specs.first_name, specs.last_name)
			password_hash = PasswordHasher().hash(specs.password)
			await conn.execute(insert_authentication, account, password_hash, specs.change_pw)
			await conn.execute(assign_admin, account)
			print("Success!")

	except Exception as e:
		print("Unable to add admin:", e)

	finally:
		await db_pool.close()

#-------------------------------------------------------------------------------

def _split_name(name):
	return [p for p in name.split(' ') if p]


def _custom_input(prompt, default_text=None):
	if default_text is not None:
		def hook():
			readline.insert_text(default_text)
			readline.redisplay()
		readline.set_pre_input_hook(hook)

	result = ""
	while not result:
		result = input(prompt).strip()

	readline.set_pre_input_hook()
	return result


def _prompt_admin_specs():
	print("Creating new admin...")
	first_name = _custom_input("First name: ").capitalize()
	last_name = input("Last name (can be left blank): ").strip().capitalize()
	suggested_login = ".".join(_split_name(first_name) + _split_name(last_name)).lower()
	login = _custom_input("User login: ", suggested_login)

	password1 = getpass("Password: ")
	password2 = getpass("Confirm password: ")
	while password1 != password2:
		print("Passwords don't match, try again:")
		password1 = getpass("Password: ")
		password2 = getpass("Confirm password: ")

	change_pw = _custom_input("Change password on next login [Y/n]? ", "n")
	while change_pw not in ('Y', 'n'):
		print("Invalid choice")
		change_pw = _custom_input("Change password on next login [Y/n]? ", "n")

	return AdminSpecs(
		first_name,
		last_name if last_name else None,
		login, password1,
		change_pw == "Y"
	)


def _load_admin_specs(import_file):
	user_schema = {
		"first_name": str,
		"last_name": "",
		"login": str,
		"password": str,
		"change_password": False
	}
	loaded = pavao.load_settings(import_file, False)
	s = loaded.get_setting("admin", user_schema)
	first = s["first_name"].strip().capitalize()
	last = s["last_name"].strip().capitalize()
	return AdminSpecs(
		first,
		last if last else None,
		s["login"].lower(),
		s["password"],
		s["change_password"]
	)

#-------------------------------------------------------------------------------

cli_parser = argparse.ArgumentParser(
	prog="auth_manager",
	description="Pavão-Auth management tool")

cli_parser.add_argument("--config-file",
	help="configuration file to use (default: application.yml)",
	metavar="FILE", default="application.yml")

subparsers = cli_parser.add_subparsers(dest="command", required=True)

subparsers.add_parser("setup",
	help="initialize the database schema and seed built-in roles")

add_admin_parser = subparsers.add_parser("add-admin",
	help="create an administrator account")

add_admin_source = add_admin_parser.add_mutually_exclusive_group(required=True)
add_admin_source.add_argument("--interactive",
	help="prompt for account details",
	action="store_true")
add_admin_source.add_argument("--import-file",
	help="load account details from a YAML file",
	metavar="FILE")

args = cli_parser.parse_args()

database_schema = {
	"host": str,
	"port": 5432,
	"database": str,
	"user": str,
	"password": ""
}

settings = pavao.load_settings(args.config_file, False)
db_settings = settings.get_setting("pavao.database.postgresql", database_schema)

#-------------------------------------------------------------------------------

if args.command == "setup":
	asyncio.run(cmd_setup(db_settings))

elif args.command == "add-admin":
	if args.interactive:
		specs = _prompt_admin_specs()
	else:
		specs = _load_admin_specs(args.import_file)

	asyncio.run(cmd_add_admin(db_settings, specs))
