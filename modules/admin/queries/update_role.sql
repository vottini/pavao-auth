
UPDATE pavao."role"
	set {column} = $1
	WHERE id = $2
	RETURNING id;

