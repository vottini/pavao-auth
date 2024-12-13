
WITH to_remove AS (
	SELECT rl.id FROM pavao."role" rl
		WHERE NOT rl.id = any($1::INTEGER[]) AND
		NOT rl.admin
)

DELETE FROM pavao.assignment assign WHERE
	assign."role" IN (SELECT id FROM to_remove) AND
	assign.account = $2;

