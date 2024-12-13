
DELETE FROM pavao.assignment
	WHERE account = $1 AND "role" in (
		SELECT id FROM pavao."role"
			WHERE admin
	)

	RETURNING account;

