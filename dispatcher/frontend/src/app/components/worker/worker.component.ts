import { Component } from '@angular/core';

import { AuthService } from '../../services/auth.service';

@Component({
    templateUrl: './worker.component.html',
})
export class WorkerComponent {
    constructor(private authService: AuthService) {}
}