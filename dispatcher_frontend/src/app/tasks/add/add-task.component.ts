import { Component, OnInit } from '@angular/core';

@Component({
    selector: 'tasks',
    templateUrl: './add-task.component.html',
    styleUrls: ['./add-task.component.css']
})
export class AddTaskComponent implements OnInit {
    taskAddingMode: string

    ngOnInit() {
        this.taskAddingMode = "script";
    }

    didSelectModeTab(mode: string) {
        this.taskAddingMode = mode;
    }

}