
DELETE FROM pavao."access"
	WHERE functionality = $1 AND "role" = $2
	RETURNING "role";

