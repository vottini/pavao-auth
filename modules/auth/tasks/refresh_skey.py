
import datetime
import asyncio
import pavao

pavao.from_module("common.py").import_item("localizer")

async def proccess(token_methods):
	validity = datetime.timedelta(days=5)
	token_methods.refresh_secret_key(validity)
	yield "Secret key refreshed"


def pavao_task():

	return {
		'package': "Pavão",
		'name': localizer.map("REFRESH_SECRET_KEY"),
		'processor': proccess,
		'schedule': '0 0 * * *'
	}

