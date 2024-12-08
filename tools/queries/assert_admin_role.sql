
WITH

existing (id) AS (
	SELECT id FROM pavao."role"
	WHERE admin
),

created (id) AS (
	INSERT INTO
		pavao."role" (name, admin)
		SELECT 'Admin', TRUE
			WHERE NOT EXISTS (
				SELECT 1 FROM pavao."role"
		  		WHERE admin
			)

	RETURNING id
)

SELECT id FROM existing UNION ALL
SELECT id from created;

