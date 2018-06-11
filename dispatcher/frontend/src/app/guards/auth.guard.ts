import { Injectable } from '@angular/core';
import { CanActivate, Router, ActivatedRouteSnapshot, RouterStateSnapshot } from '@angular/router';
import { AuthService } from '../services/auth.service';

@Injectable()
export class AuthGuard implements CanActivate {
    constructor(private authService: AuthService, private router: Router) {}

    canActivate(route: ActivatedRouteSnapshot, state: RouterStateSnapshot): boolean {
        console.log('canActivate');
        if (this.authService.refreshToken == null) {
            this.router.navigate(['login'])
            return false
        }

        let refreshTokenExpire = this.authService.refreshTokenExpire
        if (refreshTokenExpire != null && refreshTokenExpire > new Date()) {
            return true
        } else {
            this.router.navigate(['login'])
            return false
        }
    }
}