import { Component } from '@angular/core';
import { Router } from '@angular/router';

import { AuthService } from '../../services/auth.service';

@Component({
    templateUrl: './user.component.html',
    styleUrls: ['./user.component.css']
})
export class UserComponent {
    constructor(private router: Router, private authService: AuthService) {}

    logOut() {
        this.authService.logOut()
        this.router.navigate(['login'])
    }
}