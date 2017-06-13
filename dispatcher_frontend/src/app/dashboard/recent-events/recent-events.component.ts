import { Component } from '@angular/core';

@Component({
    selector: 'recent-events',
    templateUrl: 'app/dashboard/recent-events/recent-events.component.html'
})
export class RecentEventsComponent {
    logoPath = './recent-events.logo.png';
    events = [
        'Task 18a07cda1ecd started building',
        'Task 7327473e2440 started building',
        'Task 7dda1d73c66d started uploading',
        'Task 0dbfd49ada15 started uploaded'
    ];
}