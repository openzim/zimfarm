import { HttpClient, HttpErrorResponse, HttpEvent, HttpHandler, HttpInterceptor, HttpRequest } from '@angular/common/http';
import { Injectable } from '@angular/core';
import { Router } from '@angular/router';
import { BehaviorSubject, Observable, throwError as observableThrowError } from 'rxjs';
import { catchError, filter, map, switchMap, take } from 'rxjs/operators';


@Injectable({
    providedIn: 'root',
})
export class AuthService {
    constructor(private http: HttpClient, private router: Router) { }

    private getAPIRoot(): string {
        let root = window.location.origin;
        if (root.includes('localhost')) {
            root = 'https://farm.openzim.org';
        }
        return root;
    }

    authorize(username: string, password: string): Observable<AuthResponseData> {
        let body = {
            'grant_type': 'password',
            'username': username,
            'password': password
        }

        return this.http.post<AuthResponseData>(
            this.getAPIRoot() + '/api/auth/oauth2', body
        ).pipe(map(data => {
            this.accessToken = data.access_token
            this.refreshToken = data.refresh_token
            this.refreshTokenExpire = new Date(Date.now() + 30*24*3600000)
            return data
        }))
    }

    refresh(refreshToken: string): Observable<AuthResponseData> {
        let body = {
            'grant_type': 'refresh_token',
            'refresh_token': refreshToken
        }
        
        return this.http.post<AuthResponseData>(
            this.getAPIRoot() + '/api/auth/oauth2', body
        ).pipe(map(data => {
            this.accessToken = data.access_token
            this.refreshToken = data.refresh_token
            this.refreshTokenExpire = new Date(Date.now() + 30*24*3600000)
            return data
        }), catchError(error => {
            this.router.navigate(['login'])
            return observableThrowError(error)
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
    constructor(private authService: AuthService) {}

    private refreshTokenInProgress = false;
    private accessTokenSubject: BehaviorSubject<null|string> = new BehaviorSubject<null|string>(this.authService.accessToken);
    
    // https://medium.com/@alexandrubereghici/angular-tutorial-implement-refresh-token-with-httpinterceptor-bfa27b966f57
    intercept(request: HttpRequest<any>, next: HttpHandler): Observable<HttpEvent<any>> {
        if (request.url.includes('auth')) {
            return next.handle(request);
        } else {
            let requestWithToken = this.makeRequestWithToken(request, this.authService.accessToken);
            return next.handle(requestWithToken).pipe(catchError(error => {
                if (error instanceof HttpErrorResponse && error.status == 401) {
                    if (this.refreshTokenInProgress) {
                        return this.accessTokenSubject.pipe(
                            filter(accessToken => accessToken != null), 
                            take(1), 
                            switchMap(accessToken => {
                                let requestWithToken = this.makeRequestWithToken(request, accessToken);
                                return next.handle(requestWithToken)
                        }))
                    } else {
                        this.refreshTokenInProgress = true;
                        this.accessTokenSubject.next(null);
                        return this.authService.refresh(this.authService.refreshToken).pipe(switchMap(responseData => {
                            this.refreshTokenInProgress = false;
                            this.accessTokenSubject.next(responseData.access_token);
                            let requestWithToken = this.makeRequestWithToken(request, responseData.access_token);
                            return next.handle(requestWithToken)
                        }))
                    }
                } else {
                    return observableThrowError(error)
                }
            }))
        }
    }

    private makeRequestWithToken(request: HttpRequest<any>, accessToken: string): HttpRequest<any> {
        return request.clone({headers: request.headers.set('Authorization', 'Bearer ' + accessToken)})
    }
}
