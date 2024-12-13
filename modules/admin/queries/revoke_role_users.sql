
WITH to_remove AS (
	SELECT acc.id FROM pavao.account acc
		WHERE NOT acc.id = any($1::INTEGER[])
)

DELETE FROM pavao.assignment assign WHERE
	assign.account IN (SELECT id FROM to_remove) AND
	assign."role" = $2;

