import { Component, OnInit } from '@angular/core';

import { Task, TasksService } from '../../services/task.service';

@Component({
    templateUrl: './task-list.html',
    styleUrls: ['./task-list.css']
})
export class TaskListComponent implements OnInit {
    constructor(private tasksService: TasksService) { }
    tasks: Array<Task> = []

    ngOnInit() {
        this.tasksService.list().subscribe(data => {
            this.tasks = data.items;
        })
    }
}