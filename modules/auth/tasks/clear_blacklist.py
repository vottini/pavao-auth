
import asyncio
import pavao

pavao.from_module("common").import_item("localizer")

async def proccess(authorizer):
	removed = authorizer.clear_blacklist()
	yield f"{removed} expired tokens purged from blacklist"


def pavao_task(db_connection):
	if db_connection is None:
		return

	return {
		'package': "Pavão",
		'name': localizer.map("CLEAR_BLACKLIST"),
		'processor': proccess,
		'schedule': '0 0 * * *'
	}

