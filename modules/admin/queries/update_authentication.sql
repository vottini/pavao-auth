
UPDATE pavao.authentication SET
	hash = $2,
	needs_change = $3
	WHERE account = $1
	RETURNING account;

