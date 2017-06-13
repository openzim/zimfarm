import { Component, OnInit } from '@angular/core';
import { NgbModal, NgbModalRef } from '@ng-bootstrap/ng-bootstrap';

import { Task } from '../model/task';
import { TaskService } from '../model/task.service';

@Component({
    selector: 'tasks',
    templateUrl: './tasks.component.html',
    styleUrls: ['./tasks.component.css']
})
export class TasksComponent {
    constructor(
        private taskService: TaskService,
        private modalService: NgbModal
    ) {}

    private tasks: Task[]
    command: string
    private modal: NgbModalRef

    ngOnInit() {
        this.refresh()
    }

	showAddTaskModal(content: any): void {
        this.modal = this.modalService.open(content);
        this.modal.result.then((result) => {
            // closed
        }, (reason) => {
            //dismissed
        });
    }

    addTask(): void {
        this.taskService.addTask(this.command);
        this.refresh();
        console.log(this.command);
        this.modal.dismiss();
    }

    refresh(): void {
        this.taskService.getTasks().then((tasks) => this.tasks = tasks);
    }
}