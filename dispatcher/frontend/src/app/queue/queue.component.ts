import { Component } from '@angular/core';

import { AuthService } from '../services/auth.service';

@Component({
    templateUrl: './queue.component.html',
})
export class QueueComponent {
    constructor(private authService: AuthService) {}
}