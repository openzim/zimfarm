import { Component, Input } from '@angular/core';
import { Task } from '../../services/task.service';

@Component({
    selector: 'task-list-item',
    templateUrl: './task-list-item.html',
    styleUrls: ['./task-list-item.css']
})
export class TaskListItemComponent {
    @Input() task: Task;
}