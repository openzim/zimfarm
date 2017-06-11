import { Injectable } from '@angular/core';
import { Http, Headers, RequestOptions, Response } from '@angular/http';
import { Subject }    from 'rxjs/Subject';
import { JwtHelper } from 'angular2-jwt';

import 'rxjs/add/operator/toPromise';

@Injectable()
export class AuthService {
    private jwt: JwtHelper = new JwtHelper();
    scope: string[] = [];
    scopeChange: Subject<string[]> = new Subject<string[]>();

    constructor(private http: Http) {
        let token = this.getToken();
        this.decodeScope(token);
    }

    login(username: string, password: string) {
        const url = 'api/auth/login';
        let body = JSON.stringify({username: username, password: password});
        let options = new RequestOptions ({
            headers: new Headers({'Content-Type': 'application/json'})
        })
        return this.http.post('api/auth/login', body, options)
            .toPromise()
            .then(response => {
                let json  = response.json();
                if (json.success) {
                    this.setToken(json.token);
                    this.decodeScope(json.token);
                }
                return json.success
            })
            .catch(this.handleError);
    }

    private handleError(error: any): Promise<any> {
        console.error('An error occurred', error);
        return Promise.reject(error.message || error);
    }

    private decodeScope(token?: string) {
        this.scope = token == null ? [] : this.scope = this.jwt.decodeToken(token).scope;
        this.scopeChange.next(this.scope);
    }

    private getToken(): string {
        return localStorage.getItem('token');
    }

    private setToken(token: string) {
        localStorage.setItem('token', token);
    }

    logout() {
        localStorage.removeItem('token');
        this.decodeScope(null);
    }
}