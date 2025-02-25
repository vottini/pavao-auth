
INSERT INTO
	pavao."role" (name, description, code)
	VALUES ($1, $2, $3)
	RETURNING id;

