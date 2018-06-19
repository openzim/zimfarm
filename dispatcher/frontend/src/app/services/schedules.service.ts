import { Injectable } from '@angular/core';
import { HttpClient, HttpInterceptor, HttpHeaders, HttpRequest, HttpHandler, HttpEvent } from '@angular/common/http';
import { Observable, throwError } from 'rxjs';

import { apiRoot } from './config';

@Injectable({
    providedIn: 'root',
})
export class SchedulesService {
    constructor(private http: HttpClient) { }

    list(offset: number = 0, limit: number = 20) {
        return this.http.get<SchedulesListResponseData>('https://farm.openzim.org/api/schedules/')
    }
}

interface SchedulesListResponseData {
    items: Array<Schedule>;
    meta: SchedulesListMeta;
}

interface SchedulesListMeta {
    limit: number;
    skip: number;
}

interface Schedule {
    _id: string;
    category: string;
    language: string;
    offliner: string;
    schedule: Object;
    task: Object;
}