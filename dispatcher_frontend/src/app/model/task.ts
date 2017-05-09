export class Task {
	id: string;
	name: string;
	status: string;
	time: TaskTimeStamp;
	argument: TaskArgument;
	result: TaskResult;
}

export class TaskTimeStamp {
	created: Date;
	started: Date;
	finished: Date;
}

export class TaskArgument {
	keyword: string;
	positional: string;
}

export class TaskResult {
	stdout: string;
	stderr: string;
}