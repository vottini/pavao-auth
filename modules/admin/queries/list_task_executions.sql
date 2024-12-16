
SELECT
	id,
	success,
	execution_start,
	execution_end

	FROM task_execution
	WHERE task = :task AND
		DATE(execution_start) = :start AND
		execution_end IS NOT NULL;

