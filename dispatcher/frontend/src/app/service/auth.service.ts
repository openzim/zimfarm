import { Injectable } from '@angular/core';
import { Http, Headers, RequestOptions, Response } from '@angular/http';
import { Subject }    from 'rxjs/Subject';
import { Observable } from 'rxjs/Rx';
import { JwtHelper } from 'angular2-jwt';

import 'rxjs/add/operator/map';


@Injectable()
export class AuthService {
    private jwt: JwtHelper = new JwtHelper();
    scope: string[] = [];
    scopeChange: Subject<string[]> = new Subject<string[]>();

    constructor(private http: Http) {
        this.decodeScope();
    }

    get isLoggedIn(): boolean {
        let token = this.getToken();
        return token != null && !this.jwt.isTokenExpired(token);
    }

    get shouldRenewToken(): boolean {return true;}

    get username(): string {
        let decoded = this.decodeToken()
        return decoded != null ? decoded.username : null;
    }

    // http

    login(username: string, password: string): Observable<boolean> {
        return this.auth({username: username, password: password});
    }

    renew(old_token: string=null): Observable<boolean> {
        if (old_token == null) {old_token = this.getToken()}
        return this.auth({token: old_token})
    }

    private auth(header: {}): Observable<boolean> {
        let url = 'api/auth/login';
        let options = new RequestOptions ({
            headers: new Headers(header)
        });
        return this.http.post('api/auth/login', null, options)
            .map(response => {
                let json = response.json()
                this.setToken(json.token)
                return json.success
            });
    }

    // token decode

    private decodeToken() {
        let token = this.getToken();
        return token != null ? this.jwt.decodeToken(token) : null;
    }

    private decodeScope() {
        let decoded_token = this.decodeToken();
        this.scope = decoded_token == null ? [] : decoded_token.scope;
        this.scopeChange.next(this.scope);
    }

    // token persistence

    private setToken(token: string) {
        localStorage.setItem('zimfarm_token', token);
        this.decodeScope();
    }

    getToken(): string {
        return localStorage.getItem('zimfarm_token');
    }

    removeToken() {
        localStorage.removeItem('zimfarm_token');
        this.decodeScope();
    }
}