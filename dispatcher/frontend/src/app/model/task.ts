export class Task {
	command: string;
	id: string;
	name: string;
	returncode: number;
	status: string;
	result: TaskResult;
	time: TaskTimeStamp;
}

export class TaskTimeStamp {
	created: Date;
	started: Date;
	finished: Date;
}

export class TaskResult {
	stdout: string;
	stderr: string;
	error: string;
}