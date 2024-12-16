
SELECT instant, content FROM task_output
	WHERE execution = :execution
	ORDER BY instant;

