
SELECT
	acc.id,
	acc.login,
	acc.first_name,
	acc.last_name,
	acc.active,
	bool_or(COALESCE(rl."admin", FALSE)) as admin,
	acc.id = $1 as my_account

	FROM pavao.account acc
		LEFT JOIN pavao."assignment" assig ON assig.account = acc.id
		LEFT JOIN pavao."role" rl ON assig."role" = rl.id
	
	WHERE NOT acc.bot
	GROUP BY acc.id;

