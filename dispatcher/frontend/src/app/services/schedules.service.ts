import { HttpClient } from '@angular/common/http';
import { Injectable } from '@angular/core';

import { BaseService } from './base.service';

@Injectable({
    providedIn: 'root',
})
export class SchedulesService extends BaseService {
    constructor(private http: HttpClient) { super() }

    list(params: SchedulesListRequestParams) {
        return this.http.get<SchedulesListResponseData>(
            this.getAPIRoot() + '/schedules/', {params: params.toDict()})
    }

    list_old(skip: number = 0, limit: number = 20, queues: string[] = [], categories: string[] = [], 
        languages: string[] = [], name: string = "", tags: string[] = []) {
        let params = {
            skip: skip.toString(),
            limit: limit.toString()};
        if (queues.length > 0) {
            params['queue'] = queues;
        }
        if (categories.length > 0) {
            params['category'] = categories;
        }
        if (languages.length > 0) {
            params['lang'] = languages;
        }
        if (name.length > 0) {
            params['name'] = name;
        }
        if (tags.length > 0) {
            params['tag'] = tags;
        }
        return this.http.get<SchedulesListResponseData>(
            this.getAPIRoot() + '/schedules/', {params: params})
    }

    get(schedule_id_name: string) {
        let url = this.getAPIRoot() + '/schedules/' + schedule_id_name
        return this.http.get<Schedule>(url);
    }
}

export class SchedulesListRequestParams {
    name?: string

    toDict(): {} {
        let params = {}
        if (this.name && this.name.length > 0) {
            params['name'] = this.name
        }
        return params
    }
}

export interface SchedulesListResponseData {
    items: Array<Schedule>;
    meta: SchedulesListMeta;
}

export interface SchedulesListMeta {
    limit: number;
    skip: number;
    count: number;
}

export interface Schedule {
    _id: string;
    category: string;
    enabled: boolean;
    name: string;
    config: Config;
    language: Language;
    tags: [string];
}

export interface Config {
    task_name: string;
    queue: string;
    warehouse_path: string;
    offliner: ConfigOffliner;
}

export interface ConfigOffliner {
    image_name: string;
    image_tag: string;
    flags: Object;
}

export interface Language {
    code: string;
    name_en: string;
    name_native: string;
}
