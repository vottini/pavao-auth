
INSERT INTO
	pavao.access (functionality, "role")
	SELECT $1, rl.id FROM pavao."role" rl
		WHERE rl.admin
		ON CONFLICT DO NOTHING;

