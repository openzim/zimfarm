import { Injectable } from '@angular/core';
import { Http, Headers, RequestOptions, Response } from '@angular/http';
import { Observable } from 'rxjs/Rx';

import { AuthService } from './auth.service';


@Injectable()
export class TaskService {
    private urlRoot = 'https://zimfarm.chrisshwli.com/api'
    // private urlRoot = 'api'
    constructor(private http: Http, private authService: AuthService) { }

    enqueue_zimfarm_generic(image_name: string, script: string) {
        let url = this.urlRoot + '/task/zimfarm_generic'
        let body = JSON.stringify({
            image_name: image_name,
            script: script
        })
        let headers = new Headers({'Content-Type': 'application/json', 'token': this.authService.getToken()})
        let options = new RequestOptions ({headers: headers})
        return this.http.post(url, body, options);
    }

    list_tasks(limit: number, offset: number) {
        let url = this.urlRoot + '/task'
        let headers = new Headers({
            'Content-Type': 'application/json', 
            'token': this.authService.getToken(),
            limit: limit,
            offset: offset
        })
        let options = new RequestOptions ({headers: headers})
        return this.http.get(url, options).map(response => response.json());
    }

    task_detail(task_id: string) {
        let url = this.urlRoot + '/task/' + task_id
        let headers = new Headers({'Content-Type': 'application/json', 'token': this.authService.getToken()})
        let options = new RequestOptions ({headers: headers})
        return this.http.get(url, options).map(response => response.json() || {});
    }
}