import { Component, OnInit } from '@angular/core';
import { ActivatedRoute } from "@angular/router";

import { TasksService, Task, ListResponseData } from '../../services/task.service';
import { switchMap } from 'rxjs/operators';
import { Observable } from 'rxjs';

@Component({
    templateUrl: './task-detail.html',
    styleUrls: ['./task-detail.css']
})
export class TaskDetailComponent implements OnInit {
    constructor(private route: ActivatedRoute, private tasksService: TasksService) { }
    task: Observable<Task>
    task_id: string;
    task$: Observable<Task>;

    ngOnInit() {
        // this.route.paramMap.subscribe(params => {
        //     console.log(params);
        //     this.task_id = params.get('id');
        //     // this.animal = params.get("animal")
        // })

        this.task$ = this.route.paramMap.pipe(
            switchMap(params => {
                this.task_id = params.get('id');
                return this.tasksService.get(params.get('id'));
            })
        );
    }
}