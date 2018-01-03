import { HttpClient, HttpHeaders } from '@angular/common/http';
import { Observable } from 'rxjs/Observable';
import { Injectable } from '@angular/core';
import { Task } from '../class/task';
import 'rxjs/add/operator/map';


@Injectable()
export class TaskService {
    constructor(private http: HttpClient) {}

    urlRoot = 'https://farm.openzim.org/api/'
    // urlRoot = 'api/'

    listTasks(): Observable<ListTaskResponse> {
        return this.http.get<ListTaskResponse>(this.urlRoot + 'task/')
    }
}

export class ListTaskResponse {
    items: Task[]
}