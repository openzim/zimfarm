import { Injectable } from '@angular/core';
import { HttpClient, HttpInterceptor, HttpHeaders, HttpRequest, HttpHandler, HttpEvent } from '@angular/common/http';
import { Observable, throwError } from 'rxjs';
import cronstrue from 'cronstrue';

import { apiRoot, languageNames } from './const.service';
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
                item.language = languageNames[item.language]
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
    beat: Beat;
    category: string;
    language: string;
    last_run: Date;
    name: string;
    task: Object;
    total_run: number;
}

export class Beat {
    type: string;
    config: Object;

    constructor(type: string, config: Object) {
        this.type = type
        this.config = config
    }

    description(): string {
        if (this.type == 'crontab') {
            let minute = this.config['minute'] != null ? this.config['minute'] : '*'
            let hour = this.config['hour'] != null ? this.config['hour'] : '*'
            let day_of_week = this.config['day_of_week'] != null ? this.config['day_of_week'] : '*'
            let day_of_month = this.config['day_of_month'] != null ? this.config['day_of_month'] : '*'
            let month_of_year = this.config['month_of_year'] != null ? this.config['month_of_year'] : '*'
            return cronstrue.toString(Array(minute, hour, day_of_month, month_of_year, day_of_week).join(' '))
        } else {
            return '';
        }
    }
}