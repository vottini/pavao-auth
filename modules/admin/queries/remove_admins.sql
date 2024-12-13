
DELETE FROM
	pavao."assignment"
		WHERE
			"role" = $1 AND
			NOT account = ANY($2::INTEGER[]);

