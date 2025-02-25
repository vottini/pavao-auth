
SELECT
	rl.id,
	rl.code,
	rl.name

FROM pavao.account acc
	INNER JOIN pavao.assignment assig ON assig.account = acc.id
	INNER JOIN pavao."role" rl ON assig."role" = rl.id
	WHERE acc.id = $1;

