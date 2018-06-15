import { Component } from '@angular/core';
import { Router } from '@angular/router';

import { AuthService } from '../../services/auth.service';

@Component({
    templateUrl: './login.component.html',
    styleUrls: ['./login.component.css']
})
export class LoginComponent {
    constructor(private router: Router, private authService: AuthService) {}

    username: string;
    password: string;
    hideInvalidCredential: boolean = true;

    login(): void {
        this.authService.authorize(this.username, this.password).subscribe(success => {
            this.hideInvalidCredential = success
            if (success) {
                this.router.navigate([''])
            }
        });
    }

    valueChanged() {
        this.hideInvalidCredential = true
    }

}
