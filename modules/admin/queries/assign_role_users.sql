
WITH to_add AS (
	SELECT acc.id FROM pavao.account acc
		WHERE acc.id = any($1::INTEGER[])
)

INSERT INTO pavao.assignment (account, "role")
	SELECT collected.id, $2 FROM to_add collected
	ON CONFLICT DO NOTHING;

