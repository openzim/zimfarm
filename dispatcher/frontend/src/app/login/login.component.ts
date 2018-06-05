import { Component } from '@angular/core';
import { Router } from '@angular/router';

import { AuthService } from '../services/auth.service';

@Component({
    templateUrl: './login.component.html',
    styleUrls: ['./login.component.css']
})
export class LoginComponent {
    constructor(
        private router: Router,
        private authService: AuthService) {}

    username: string;
    password: string;

    login(): void {
        this.authService.authorize(this.username, this.password).subscribe(success => {
            if (success) {
                this.router.navigate(['/'])
            }
        });
    }

}
