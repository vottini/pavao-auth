
DELETE FROM pavao."role"
	WHERE id = $1
	RETURNING id;

