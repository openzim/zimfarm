import { Component } from '@angular/core';

import { AuthService } from '../../services/auth.service';

@Component({
    templateUrl: './schedule.component.html',
})
export class ScheduleComponent {
    constructor(private authService: AuthService) {}
}