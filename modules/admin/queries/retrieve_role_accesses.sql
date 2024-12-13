
SELECT
	func.id,
	func.name,
	func.package

	from pavao."role" rl
		INNER JOIN pavao.access acs ON acs."role" = rl.id
		INNER JOIN pavao.functionality func ON acs.functionality = func.id
		WHERE func.enabled AND rl.id = $1;

