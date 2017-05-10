import { Component, OnInit } from '@angular/core';
import { NgbModal } from '@ng-bootstrap/ng-bootstrap';

import { Task } from '../model/task';
import { TaskService } from '../model/task.service';

@Component({
    selector: 'tasks',
    templateUrl: 'app/tasks/tasks.component.html'
})
export class TasksComponent {
    constructor(
        private taskService: TaskService,
        private modalService: NgbModal
    ) {}

    private tasks: Task[]

    ngOnInit() {
        this.refresh()
    }

	addTask(content: any): void {
        console.log('addTask');
        this.modalService.open(content).result.then((result) => {
            console.log(result);
        }, (reason) => {
            console.log(reason);
        });
    }

    refresh(): void {
        this.taskService.getTasks().then((tasks) => this.tasks = tasks);
    }
}