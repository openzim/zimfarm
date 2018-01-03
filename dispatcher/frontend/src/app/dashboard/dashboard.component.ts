import { Component, OnInit } from '@angular/core';
import { TaskService } from '../service/task.service';
import { Task } from '../class/task';


@Component({
    selector: 'dashboard',
    templateUrl: './dashboard.component.html',
    styleUrls: ['./dashboard.component.css']
})
export class DashboardComponent {
    tasks: Task[] = []

    constructor(private taskService: TaskService) {}

    ngOnInit() {
        this.taskService.listTasks().subscribe(response => {
            this.tasks = response.items
        })
    }

    getTaskStatusColor() {
        return 'ff0000'
    }

    color = 'ff0000'
}