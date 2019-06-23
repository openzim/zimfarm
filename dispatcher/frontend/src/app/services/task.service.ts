import { HttpClient } from '@angular/common/http';
import { Injectable } from '@angular/core';
import { Observable } from 'rxjs';

import { BaseService } from './base.service';

@Injectable({
    providedIn: 'root',
})
export class TasksService extends BaseService {
    constructor(private http: HttpClient) { super() }

    list(skip: number = 0, limit: number = 100): Observable<ListResponseData> {
        let params = {skip: skip.toString(), limit: limit.toString()}
        return this.http.get<ListResponseData>(this.getAPIRoot() + '/tasks/', {params: params});
    }
    
    get(task_id: string): Observable<Task> {
        return this.http.get<Task>(this.getAPIRoot() + '/tasks/' + task_id);
    }
}

export interface ListResponseData {
    items: Array<Task>;
    meta: ListMeta;
}

export interface ListMeta {
    limit: number;
    skip: number;
}

export interface Task {
    _id: string;
    status: string;
    schedule: Schedule;
}

export interface Schedule {
    _id: string;
    name: string;
}
