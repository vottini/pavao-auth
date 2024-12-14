
SELECT COUNT(*) FROM
	pavao.functionality func
		INNER JOIN pavao."access" acc ON acc.functionality = func.id
		INNER JOIN pavao."role" rl ON acc."role" = rl.id

	WHERE
		func.id = $1 AND
		rl.admin;

