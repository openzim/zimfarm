import { Injectable }    from '@angular/core';
import { Headers, Http } from '@angular/http';

import 'rxjs/add/operator/toPromise';

import { Task } from './task';

@Injectable()
export class TaskService {
    private headers = new Headers({'Content-Type': 'application/json'});
    private url = 'api/task';

	constructor(private http: Http) { }

	getTasks(): Promise<Task[]> {
        return this.http.get(this.url)
               .toPromise()
               .then(response => response.json().data)
               .catch(this.handleError);
	}

	private handleError(error: any): Promise<any> {
        console.error('An error occurred', error);
        return Promise.reject(error.message || error);
    }
}