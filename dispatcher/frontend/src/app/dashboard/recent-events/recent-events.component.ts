import { Component } from '@angular/core';

@Component({
    selector: 'recent-events',
    templateUrl: './recent-events.component.html'
})
export class RecentEventsComponent {
    events = [
        'Task 18a07cda1ecd started building',
        'Task 7327473e2440 started building',
        'Task 7dda1d73c66d started uploading',
        'Task 0dbfd49ada15 started uploaded'
    ];
}