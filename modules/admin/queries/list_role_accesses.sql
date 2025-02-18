
WITH role_access AS (
	SELECT acs.functionality, acs."role"
		FROM pavao."access" acs
			INNER JOIN pavao."role" rl ON acs."role" = rl.id
			WHERE rl.id = $1
)

SELECT
	func.id,
	func.package AS package,
	func.name AS functionality,
	racs."role" IS NOT NULL AS accessable

	FROM pavao.functionality func
		LEFT JOIN role_access racs ON racs.functionality = func.id;

