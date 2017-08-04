import { Injectable, OnDestroy } from '@angular/core';
import { Http, Headers, RequestOptions, Response } from '@angular/http';
import { Observable, Subscription } from 'rxjs/Rx';
import { Subject } from 'rxjs/Subject';
import 'rxjs/add/operator/map';
import { JwtHelper } from 'angular2-jwt';

import { User } from '../model/user';


@Injectable()
export class AuthService implements OnDestroy {
    private urlRoot = 'https://zimfarm.chrisshwli.com/api'
    // private urlRoot = 'api'
    
    private jwt: JwtHelper = new JwtHelper();
    private timer: Observable<number>;
    private timerSubscription: Subscription;

    user: User;
    userChanged = new Subject<User>();

    constructor(private http: Http) {
        let token = this.getToken()
        if (token != null) {
            this.decode(token)
        }
    }

    ngOnDestroy(){
        this.timerSubscription.unsubscribe();
    }

    get isLoggedIn(): boolean {
        let token = this.getToken();
        return token != null && !this.jwt.isTokenExpired(token);
    }

    login(username: string, password: string): Observable<boolean> {
        let url = this.urlRoot + '/auth/login'
        let headers = new Headers({'username': username, 'password': password})
        let options = new RequestOptions ({headers: headers})
        return this.http.post(url, null, options)
            .map(response => {
                let token = response.json()['token']
                if (token) {
                    this.setToken(token)
                    this.decode(token)
                    return true
                } else {
                    return false;
                }
            });
    }

    renew(token: string): Observable<boolean> {
        let url = this.urlRoot + '/auth/renew'
        let headers = new Headers({'token': token})
        let options = new RequestOptions ({headers: headers})
        return this.http.post(url, null, options)
            .map(response => {
                let token = response.json()['token']
                if (token) {
                    this.setToken(token)
                    this.decode(token)
                    return true
                } else {
                    return false;
                }
            });
    }

    logout() {
        this.removeToken()
        this.user = null
        this.userChanged.next(this.user)
    }

    // token decode

    private decode(token: string) {
        let decoded = this.jwt.decodeToken(token)
        let expiresIn = this.jwt.getTokenExpirationDate(token).getTime() - (new Date()).getTime()
        this.timer = Observable.timer(expiresIn - 1000 * 60 * 10)
        this.timerSubscription = this.timer.subscribe(_ => {
            this.renew(this.getToken()).subscribe(renewed => {
                console.log('token renewed' + renewed);
            })
        })

        let username = String(decoded.username)
        let isAdmin = Boolean(decoded.scope.isAdmin)

        this.user = new User(username, isAdmin)
        this.userChanged.next(this.user)
    }

    // token management

    private setToken(token: string) {
        localStorage.setItem('zimfarm_token', token)
    }

    getToken(): string {
        return localStorage.getItem('zimfarm_token')
    }

    private removeToken() {
        localStorage.removeItem('zimfarm_token')
    }
}