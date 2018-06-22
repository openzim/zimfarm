import { Injectable } from '@angular/core';
import { Router } from '@angular/router';
import { HttpClient, HttpInterceptor, HttpHeaders, HttpRequest, HttpHandler, HttpEvent, HttpErrorResponse } from '@angular/common/http';
import { Observable, defer } from 'rxjs';
import { tap, catchError, map, switchMap } from 'rxjs/operators';

import { apiRoot } from './config';

@Injectable({
    providedIn: 'root',
})
export class AuthService {
    constructor(private http: HttpClient) { }

    authorize(username: string, password: string): Observable<AuthResponseData> {
        let header = new HttpHeaders({
            'username': username,
            'password': password
        })

        return this.http.post<AuthResponseData>(
            apiRoot + '/api/auth/authorize', null, {headers: header}
        ).pipe(map(data => {
            this.accessToken = data.access_token
            this.refreshToken = data.refresh_token
            this.refreshTokenExpire = new Date(Date.now() + 30*24*3600000)
            return data
        }))
    }

    refresh(refreshToken: string): Observable<AuthResponseData> {
        let header = new HttpHeaders({'refresh-token': refreshToken})
        
        return this.http.post<AuthResponseData>(
            apiRoot + '/api/auth/token', null, {headers: header}
        ).pipe(map(data => {
            this.accessToken = data.access_token
            this.refreshToken = data.refresh_token
            this.refreshTokenExpire = new Date(Date.now() + 30*24*3600000)
            return data
        }), catchError((error, caught) => {
            // redirect back to login
            return Observable.throw(error)
        }))
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
    constructor(private authService: AuthService, private router: Router) {}

    intercept(request: HttpRequest<any>, next: HttpHandler): Observable<HttpEvent<any>> {
        if (request.url.includes('auth')) {
            return next.handle(request);
        } else {
            let requestWithToken = request.clone({headers: request.headers.set('token', this.authService.accessToken)})
            return next.handle(requestWithToken).pipe(catchError((error, _) => {
                if (error instanceof HttpErrorResponse) {
                    if (error.status == 401) {
                        this.authService.refresh(this.authService.refreshToken).pipe(switchMap((data, index) => {
                            let requestWithToken = request.clone({headers: request.headers.set('token', this.authService.accessToken)})
                            return next.handle(requestWithToken)
                        }))
                        console.log('error');
                    }
                    return Observable.throw(error)
                } else {
                    return Observable.throw(error)
                }
            }))
        }
    }
}
