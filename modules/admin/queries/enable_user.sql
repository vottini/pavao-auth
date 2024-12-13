
UPDATE pavao.account
	SET active = $2
	WHERE id = $1
	RETURNING id;

