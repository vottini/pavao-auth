
SELECT
	acc.id,
	CONCAT_WS(' ', acc.first_name, acc.last_name) AS full_name

	FROM pavao."role" rl
		INNER JOIN pavao."assignment" assig ON assig."role" = rl.id
		INNER JOIN pavao.account acc ON assig.account = acc.id
		WHERE rl.id = $1 AND acc.active;

