import { Component, OnInit } from '@angular/core';
import { Router, ActivatedRoute } from '@angular/router';

import { Task } from '../../model/task';
import { TaskService } from '../../service/task.service';

@Component({
    selector: 'tasks',
    templateUrl: './list-tasks.component.html',
    styleUrls: ['./../tasks.common.css','./list-tasks.component.css']
})
export class ListTasksComponent implements OnInit {
    tasks: Task[] = []

    constructor(
        private route: ActivatedRoute,
        private router: Router,
        private taskService: TaskService
    ){}

    ngOnInit(): void {
        this.refreshTasks();
    }

    refreshTasks(): void {
        this.taskService.list_tasks(10,0)
            .subscribe(results => {
                this.tasks = results.tasks;
                console.log(results.tasks);
            }, error => {
                if (error.status == 401) {
                    this.router.navigateByUrl('/login');
                } else {
                }
            }    
        )
    }
}