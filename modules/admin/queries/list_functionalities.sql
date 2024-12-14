
SELECT
	id,
	COALESCE(package, '') AS package,
	name AS functionality,
	enabled

	FROM pavao.functionality;

