
SELECT
	rl.id,
	rl.name,
	assign.account IS NOT NULL AS assigned

	FROM pavao."role" rl
		LEFT JOIN pavao.assignment assign ON
			assign."role" = rl.id AND
			assign.account = $1

	WHERE rl.code <> 'PAVAO::ADMIN_ROLE';

