import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { getAPIRoot } from './config';

@Injectable({
    providedIn: 'root',
})
export class TasksService {
    constructor(private http: HttpClient) { }

    private getTasksAPIRoot(): string {
        return getAPIRoot() + '/tasks/'
    }

    list(skip: number = 0, limit: number = 100): Observable<ListResponseData> {
        let params = {
            skip: skip.toString(),
            limit: limit.toString()};
        return this.http.get<ListResponseData>(this.getTasksAPIRoot(), {params: params});
    }
    
    get(task_id: string): Observable<Task> {
        return this.http.get<Task>(this.getTasksAPIRoot() + task_id);
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
