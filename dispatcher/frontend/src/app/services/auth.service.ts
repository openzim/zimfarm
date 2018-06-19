import { Injectable } from '@angular/core';
import { HttpClient, HttpInterceptor, HttpHeaders, HttpRequest, HttpHandler, HttpEvent } from '@angular/common/http';
import { Observable } from 'rxjs';

import { apiRoot } from './config';

@Injectable({
    providedIn: 'root',
})
export class AuthService {

    constructor(private http: HttpClient) { }

    authorize(username: string, password: string): Observable<boolean> {
        return new Observable(observer => {
            let header = new HttpHeaders({
                'username': username,
                'password': password
            });

            this.http.post<AuthResponseData>(
                apiRoot + '/api/auth/authorize', null, {headers: header}
            ).subscribe(data => {
                this.accessToken = data.access_token
                this.refreshToken = data.refresh_token
                this.refreshTokenExpire = new Date(Date.now() + 30*24*3600000)

                observer.next(true)
                observer.complete()
            }, error => {
                observer.next(false)
                observer.complete()
            })
        });
    }

    logOut() {
        localStorage.removeItem('zimfarm.access_token');
        localStorage.removeItem('zimfarm.refresh_token');
        localStorage.removeItem('zimfarm.refresh_token_expire');
    }

    get accessToken(): string {return localStorage.getItem('zimfarm.access_token')}
    set accessToken(token: string) {localStorage.setItem('zimfarm.access_token', token)}

    get refreshToken(): string {return localStorage.getItem('zimfarm.refresh_token')}
    set refreshToken(token: string) {localStorage.setItem('zimfarm.refresh_token', token)}

    get refreshTokenExpire(): Date {
        let data = localStorage.getItem('zimfarm.refresh_token_expire')
        return data == null ? null : new Date(data)}
    set refreshTokenExpire(date: Date) {localStorage.setItem('zimfarm.refresh_token_expire', date.toString())}
}

interface AuthResponseData {
    access_token: string;
    refresh_token: string;
}

@Injectable()
export class AccessTokenInterceptor implements HttpInterceptor {
    constructor(private authService: AuthService) {}

    intercept(request: HttpRequest<any>, next: HttpHandler): Observable<HttpEvent<any>> {
        if (request.url.includes('/auth/authorize')) {
            return next.handle(request);
        } else {
            let duplicatedRequest = request.clone({
                headers: request.headers.set('token', this.authService.accessToken)})
            return next.handle(duplicatedRequest);
        }
    }
}
