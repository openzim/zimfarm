import { Component, OnInit } from '@angular/core';
import { Router, ActivatedRoute, Params } from '@angular/router';
import { Location } from '@angular/common';

import { TaskService } from '../../service/task.service';


@Component({
    selector: 'task-detail',
    templateUrl: './task-detail.component.html',
    styleUrls: ['./../tasks.common.css', './task-detail.component.css']
})

export class TaskDetailComponent implements OnInit {
    task: {}
    
    constructor(
        private route: ActivatedRoute,
        private router: Router,
        private location: Location,
        private taskService: TaskService
    ) {}

    ngOnInit(): void {
        this.route.params.subscribe(params => {
            this.getTaskDetail(params['id'])
        })
    }

    refresh() {
        let id = this.task["id"];
        if (id != null) {
            this.getTaskDetail(id);
        }
    }

    getTaskDetail(id: string) {
        this.taskService.task_detail(id)
            .subscribe(task => {
                this.task = task;
            }, error => {
                if (error.status == 401) {
                    this.router.navigateByUrl('/login');
                } else {
                }
            }
        )
    }

    goBack(): void {
        this.router.navigate(['../', {relativeTo: this.route}]);
    } 
}