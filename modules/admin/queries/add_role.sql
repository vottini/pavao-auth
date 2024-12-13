
INSERT INTO
	pavao."role" (name, description)
	VALUES ($1, $2)
	RETURNING id;

