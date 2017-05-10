import { Injectable }    from '@angular/core';
import { Http, Headers, RequestOptions } from '@angular/http';

import 'rxjs/add/operator/toPromise';

import { Task } from './task';

@Injectable()
export class TaskService {
    private headers = new Headers({'Content-Type': 'application/json'});
    constructor(private http: Http) { }

    getTasks(): Promise<Task[]> {
        const url = 'api/task';
        return this.http.get(url)
               .toPromise()
               .then(response => response.json() as Task[])
               .catch(this.handleError);
    }

    getTask(id: string): Promise<Task> {
        const url = 'api/task/'+id;
        return this.http.get(url)
               .toPromise()
               .then(response => response.json() as Task)
               .catch(this.handleError);
    }

    addTask(command: string): Promise<Task> {
        const url = 'api/task/enqueue/subprocess';
        let body = JSON.stringify({
            'command': command
        });
        let options = new RequestOptions ({
            headers: this.headers
        })
        console.log(body);
        return this.http.post(url, body, options)
               .toPromise()
               .then(response => response.json() as Task)
               .catch(this.handleError);
    }

    private handleError(error: any): Promise<any> {
        console.error('An error occurred', error);
        return Promise.reject(error.message || error);
    }
}