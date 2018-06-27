import { Component, OnInit } from '@angular/core';
import { Router } from '@angular/router';

import { AuthService } from '../../services/auth.service';
import { catchError } from 'rxjs/operators';

@Component({
    templateUrl: './login.component.html',
    styleUrls: ['./login.component.css']
})
export class LoginComponent implements OnInit {
    constructor(private router: Router, private authService: AuthService) {}

    ngOnInit() {
        this.authService.logOut()
    }

    username: string;
    password: string;
    hideInvalidCredential: boolean = true;

    login(): void {
        this.authService.authorize(this.username, this.password).subscribe(data => {
            this.hideInvalidCredential = true
            this.router.navigate([''])
        }, error => {
            this.hideInvalidCredential = false
        })
    }

    valueChanged() {
        this.hideInvalidCredential = true
    }

}
