
SELECT id
	FROM pavao.functionality
	WHERE
		package = $1 AND
		name = $2;

