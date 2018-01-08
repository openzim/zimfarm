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
            response.items.forEach(item => {
                if (item.finished != null) {
                    item.elapsed = (Date.parse(item.finished) - Date.parse(item.created)) / 1000
                }
            })
            this.tasks = response.items
        })
    }
}