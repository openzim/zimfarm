import { Injectable } from '@angular/core';
import { HttpClient, HttpInterceptor, HttpHeaders, HttpRequest, HttpHandler, HttpEvent } from '@angular/common/http';
import { Observable, throwError } from 'rxjs';
import { catchError, map } from 'rxjs/operators';

@Injectable({
    providedIn: 'root',
})
export class AuthService {

    constructor(private http: HttpClient) { }

    authorize(username: string, password: string): Observable<Boolean> {
        return new Observable(observer => {
            let header = new HttpHeaders({
                'username': username,
                'password': password
            });

            this.http.post<AuthResponseData>(
                'https://farm.openzim.org/api/auth/authorize', '', {headers: header}
            ).subscribe(data => {
                this.accessToken = data.access_token
                this.refreshToken = data.refresh_token
                this.refreshTokenExpire = new Date(Date.now() + 30*24*3600000);

                observer.next(true);
                observer.complete();
            }, error => {
                observer.next(false);
                observer.complete();
            })
        });
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

// export class AuthInterceptor implements HttpInterceptor {
//     intercept(request: HttpRequest<any>, next: HttpHandler): Observable<HttpEvent<any>> {
//         return next.handle(request);
//     }
// }

