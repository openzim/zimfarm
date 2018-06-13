import { Component } from '@angular/core';

import { AuthService } from '../../services/auth.service';

@Component({
    templateUrl: './log.component.html',
})
export class LogComponent {
    constructor(private authService: AuthService) {}
}