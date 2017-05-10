import 'rxjs/add/operator/switchMap';
import { Component, OnInit } from '@angular/core';
import { ActivatedRoute, Params } from '@angular/router';
import { Location } from '@angular/common';

import { Task } from '../model/task';
import { TaskService } from '../model/task.service';

@Component({
    selector: 'task-detail',
    templateUrl: 'app/tasks/task-detail.component.html'
})

export class TaskDetailComponent {
    task: Task;    
    
    constructor(
        private taskService: TaskService,
        private route: ActivatedRoute,
        private location: Location
    ) {}

    ngOnInit(): void {
        this.refresh();
    }

    refresh():void {
        this.route.params
            .switchMap((params: Params) => this.taskService.getTask(params['id']))
            .subscribe(task => this.task = task);
    }

    goBack(): void {
        this.location.back();
    } 
}