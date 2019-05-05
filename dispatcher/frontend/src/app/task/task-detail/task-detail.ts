import { Component, OnInit } from '@angular/core';
import { ActivatedRoute } from '@angular/router';
import { Observable } from 'rxjs';
import { switchMap } from 'rxjs/operators';

import { Task, TasksService } from '../../services/task.service';

@Component({
    templateUrl: './task-detail.html',
    styleUrls: ['./task-detail.css']
})
export class TaskDetailComponent implements OnInit {
    constructor(private route: ActivatedRoute, private tasksService: TasksService) { }
    task$: Observable<Task>;

    ngOnInit() {
        this.task$ = this.route.paramMap.pipe(
            switchMap(params => {
                return this.tasksService.get(params.get('id'));
            })
        );
    }
}