
INSERT INTO
	pavao.functionality (package, name)
	VALUES ($1, $2) RETURNING id;

