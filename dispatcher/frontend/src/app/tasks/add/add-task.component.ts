import { Component, OnInit } from '@angular/core';
import { Router, ActivatedRoute } from '@angular/router';

import { TaskService } from '../../service/task.service';

@Component({
    selector: 'add-task',
    templateUrl: './add-task.component.html',
    styleUrls: ['./add-task.component.css']
})
export class AddTaskComponent implements OnInit {
    tabNames = ['mwoffliner', 'sotoki', 'youtube', 'gutenberg', 'phet', 'wikihow', 'ted'];
    activaTabName: string

    zimfarmGenericTask = new ZimfarmGenericTask();

    constructor(
        private route: ActivatedRoute,
        private router: Router,
        private taskService: TaskService
    ){}

    ngOnInit() {
        this.activaTabName = this.tabNames[0];
    }

    didSelectTab(name: string) {
        this.activaTabName = name;
    }

    addTaskByScript() {
        this.taskService.enqueue_zimfarm_generic(
                this.zimfarmGenericTask.containerName, 
                this.zimfarmGenericTask.script
            )
            .subscribe(result => {
                this.router.navigate(['../', {relativeTo: this.route}]);
            }, error => {
                this.zimfarmGenericTask.enqueueSuccess = false;
                if (error.status == 401) {
                    this.router.navigateByUrl('/login');
                } else {
                    this.zimfarmGenericTask.responseCode = error.status;
                }
            }
        )
    }
}

class ZimfarmGenericTask {
    containerName: string
    script: string
    enqueueSuccess: boolean = true
    responseCode: number
}