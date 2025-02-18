
import asyncio
import pavao

pavao.from_module("common.py").import_item("localizer")

purge_query = """

	WITH deleted AS (
		DELETE FROM pavao.refresh_token
			WHERE expiration < NOW()
			RETURNING *)

	SELECT COUNT(*) FROM deleted;

"""

async def proccess(pg_pool):
	async with pg_pool.acquire() as connection:
		purged = await connection.fetchval(purge_query)
		yield f"{purged} refresh token(s) purged"


def pavao_task():

	return {
		'package': "Pavão",
		'name': localizer.map("PURGE_EXPIRED_TOKENS"),
		'processor': proccess,
		'schedule': '0 * * * *'
	}

