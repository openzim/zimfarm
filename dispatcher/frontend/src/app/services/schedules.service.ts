import { Injectable } from '@angular/core';
import { HttpClient, HttpInterceptor, HttpHeaders, HttpRequest, HttpHandler, HttpEvent } from '@angular/common/http';
import { Observable, throwError } from 'rxjs';
import cronstrue from 'cronstrue';

import { apiRoot } from './config';
import { map } from 'rxjs/operators';

@Injectable({
    providedIn: 'root',
})
export class SchedulesService {
    constructor(private http: HttpClient) { }

    list(skip: number = 0, limit: number = 20) {
        return this.http.get<SchedulesListResponseData>(
            apiRoot + '/api/schedules/', 
            {
                params: {
                    skip: skip.toString(),
                    limit: limit.toString()
                }
            }
        ).pipe(map(data => {
            for (let item of data.items) {
                item.celery_queue = item['celery']['queue'];
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
    celery_queue: string;
    enabled: boolean;
    language: Language;
    name: string;
    tags: [string];
}

export interface Language {
    code: string;
    name_en: string;
    name_native: string;
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

export class BeatConfig {
    config: Object;
    description: string;

    constructor(config: Object) {this.config = config}
    updateDescription(): void {}
}

export class CrontabBeatConfig extends BeatConfig {
    get minute(): string {return this.getValue('minute')}
    set minute(value: string) {this.config['minute'] = value}
    get hour(): string {return this.getValue('hour')}
    set hour(value: string) {this.config['hour'] = value}
    get day_of_week(): string {return this.getValue('day_of_week')}
    set day_of_week(value: string) {this.config['day_of_week'] = value}
    get day_of_month(): string {return this.getValue('day_of_month')}
    set day_of_month(value: string) {this.config['day_of_month'] = value}
    get month_of_year(): string {return this.getValue('month_of_year')}
    set month_of_year(value: string) {this.config['month_of_year'] = value}

    constructor(config: Object) {
        super(config)
        this.updateDescription()
    }
    private getValue(name: string) {
        let value = this.config[name]
        return value != null && value != '' ? this.config[name] : '*'
    }

    updateDescription(): void {
        this.description = cronstrue.toString(Array(
            this.minute,
            this.hour,
            this.day_of_month,
            this.month_of_year,
            this.day_of_week
        ).join(' '))
    }
}