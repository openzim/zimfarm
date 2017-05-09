import { Component, OnInit } from '@angular/core';

import { Task } from '../model/task';
import { TaskService } from '../model/task.service';

@Component({
    selector: 'tasks',
    templateUrl: 'app/tasks/tasks.component.html'
})
export class TasksComponent {
    constructor(
        private taskService: TaskService
    ) {}
	enqueue(): void {
        console.log('enqueued');
    }

    refresh(): void {
        console.log('refresh');
        this.taskService.getTasks().then((tasks) => console.log(tasks));
    }
}