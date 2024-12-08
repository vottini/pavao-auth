
import os
import asyncio
import asyncpg
from dataclasses import dataclass
from argon2 import PasswordHasher
import pavao

script_path = os.path.dirname(os.path.realpath(__file__))
localization_dir = os.path.join(script_path, "localization")

@dataclass
class AdminSpecs:
	first_name: str
	last_name: str
	login: str
	password: str
	change_pw: bool


get_login_count = pavao.include("queries/get_login_count.sql")
insert_user = pavao.include("queries/insert_user.sql")
insert_authentication = pavao.include("queries/insert_authentication.sql")
assert_admin_role = pavao.include("queries/assert_admin_role.sql")
assign_admin = pavao.include("queries/assign_admin.sql")


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

			await db_connection.execute(assert_admin_role)
			await db_connection.execute(assign_admin, account)
			print("Success!")

	except Exception as e:
		print("Unable to add login: ", e)

	finally:
		await db_pool.close()

