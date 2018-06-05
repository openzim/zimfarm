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
                observer.next(true);
                observer.complete();
            }, error => {
                observer.next(false);
                observer.complete();
            })
        });
    }
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

