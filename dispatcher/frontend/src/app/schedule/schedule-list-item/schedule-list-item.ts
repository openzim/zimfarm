import { Component, Input } from '@angular/core';
import { Schedule } from '../../services/task.service';

@Component({
    selector: 'schedule-list-item',
    templateUrl: './schedule-list-item.html',
    styleUrls: ['./schedule-list-item.css']
})
export class ScheduleListItemComponent {
    @Input() schedule: Schedule;
}