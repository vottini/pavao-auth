
WITH

existing (id) AS (
	SELECT id FROM pavao."role"
	WHERE code = $1
),

created (id) AS (
	INSERT INTO
		pavao."role" (code, name, description)
		SELECT $1, $2, $3
			WHERE NOT EXISTS (
				SELECT 1 FROM pavao."role"
		  		WHERE code = $1
			)

	RETURNING id
)

SELECT id FROM existing UNION ALL
SELECT id from created;

