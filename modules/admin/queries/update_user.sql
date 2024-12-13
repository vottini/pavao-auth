
UPDATE pavao."account"
	set {column_name} = $1
	WHERE
		id = $2 AND
		{column_name} <> COALESCE($1, '');

