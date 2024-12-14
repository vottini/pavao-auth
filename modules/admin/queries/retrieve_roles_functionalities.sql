
SELECT
	func.package AS package,
	func."name" AS functionality,
	rl."name" AS "allowing_role"

	FROM pavao."access" acs
		INNER JOIN pavao.functionality func ON func.id = acs.functionality
		INNER JOIN pavao."role" rl ON acs."role" = rl.id

	WHERE rl.id = ANY($1::INTEGER[])
	ORDER BY func.package;

