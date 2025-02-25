
INSERT INTO
	pavao.access (functionality, "role")
	VALUES ($1, $2)
	ON CONFLICT DO NOTHING;

