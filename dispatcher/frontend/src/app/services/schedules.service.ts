import { Injectable } from '@angular/core';
import { HttpClient, HttpInterceptor, HttpHeaders, HttpRequest, HttpHandler, HttpEvent } from '@angular/common/http';
import { Observable, throwError } from 'rxjs';

import { apiRoot } from './config';
import { map } from 'rxjs/operators';

@Injectable({
    providedIn: 'root',
})
export class SchedulesService {
    constructor(private http: HttpClient) { }

    list(skip: number = 0, limit: number = 20) {
        return this.http.get<SchedulesListResponseData>(
            'https://farm.openzim.org/api/schedules/', 
            {
                params: {
                    skip: skip.toString(),
                    limit: limit.toString()
                }
            }
        ).pipe(map(data => {
            for (let item of data.items) {
                item.beat = new Beat(item.beat.type, item.beat.config);
            }
            return data
        }))
    }
}

export interface SchedulesListResponseData {
    items: Array<Schedule>;
    meta: SchedulesListMeta;
}

export interface SchedulesListMeta {
    limit: number;
    skip: number;
}

export interface Schedule {
    _id: string;
    category: string;
    language: string;
    offliner: string;
    beat: Beat;
    task: Object;
}

export class Beat {
    type: string;
    config: Object;

    constructor(type: string, config: Object) {
        this.type = type
        this.config = config
    }

    description(): string {
        return `${this.type}(day_of_month=${this.config['day_of_month']})`
    }
}