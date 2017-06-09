import { Component, OnInit } from '@angular/core';
import { Router, ActivatedRoute } from '@angular/router';

import { AuthService } from '../service/auth.service';

@Component({
    selector: 'login',
    templateUrl: 'app/login/login.component.html',
    styleUrls: ['app/login/login.component.css']
})
export class LoginComponent implements OnInit {
    model: any = {};
    loading = false;
    authFailed = false;
    returnUrl: string;

    constructor(
        private route: ActivatedRoute,
        private router: Router,
        private authService: AuthService,
    ){}

    ngOnInit() {
        this.returnUrl = this.route.snapshot.queryParams['returnUrl'] || '/';
        this.authService.logout();
    }

    login(): void {
        this.loading = true;
        this.authService.login(this.model.username, this.model.password)
            .then((success) => {
                this.loading = false;
                if (success) {
                    this.authFailed = false;
                    console.log(this.returnUrl);
                    this.router.navigate([this.returnUrl]);
                } else {
                    this.authFailed = true;
                }
            });
    }
	
}