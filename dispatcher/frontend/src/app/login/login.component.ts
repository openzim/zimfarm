import { Component, OnInit } from '@angular/core';
import { Router, ActivatedRoute } from '@angular/router';

import { AuthService } from '../service/auth.service';

@Component({
    selector: 'login',
    templateUrl: './login.component.html',
    styleUrls: ['./login.component.css']
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
            .subscribe(success => {
                this.loading = false;
                this.authFailed = false;
                this.router.navigate([this.returnUrl]);
            }, error => {
                this.loading = false;
                this.authFailed = true;
            }    
        )
    }
}