import { Injectable } from '@angular/core';
import { Http, Headers, RequestOptions, Response } from '@angular/http';
import { Observable } from 'rxjs/Observable';

import 'rxjs/add/operator/toPromise';

@Injectable()
export class AuthService {
    constructor(private http: Http) { }

    login(username: string, password: string) {
        const url = 'api/auth/login';
        let body = JSON.stringify({username: username, password: password});
        let options = new RequestOptions ({
            headers: new Headers({'Content-Type': 'application/json'});
        })
        console.log(body);
        return this.http.post('api/auth/login', body, options)
            .toPromise()
            .then(response => {
                let json  = response.json();
                if (json.success) {
                    localStorage.setItem('token', json.token);
                }
                return json.success
            })
            .catch(this.handleError);
    }

    private handleError(error: any): Promise<any> {
        console.error('An error occurred', error);
        return Promise.reject(error.message || error);
    }

    logout() {
        localStorage.removeItem('token');
    }
}