
INSERT INTO
	pavao."assignment" (account, "role")
		SELECT id, $1 FROM pavao.account
		WHERE id = ANY($2::integer[])

	ON CONFLICT DO NOTHING;

