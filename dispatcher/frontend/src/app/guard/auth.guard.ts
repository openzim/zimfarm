import { Injectable } from '@angular/core';
import { Router, CanActivate, ActivatedRouteSnapshot, RouterStateSnapshot } from '@angular/router';

import { AuthService } from '../service/auth.service';

@Injectable()
export class AuthGuard implements CanActivate {
    constructor(private router: Router, private authService: AuthService) { }

    canActivate(route: ActivatedRouteSnapshot, state: RouterStateSnapshot) {
        if (this.authService.isLoggedIn) {
            return true;
        } else {
            if (state.url == '/tasks') {
                this.router.navigate(['/login']);
            } else {
                this.router.navigate(['/login'], { queryParams: { returnUrl: state.url }});
            }
            return false;
        }
    }
}