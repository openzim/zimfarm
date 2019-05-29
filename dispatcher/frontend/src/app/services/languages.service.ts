import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';

import { getAPIRoot } from './config';

export interface Language {
    code: string;
    name_en: string;
    name_native: string;
}

export interface LanguagesListResponseData {
    items: Array<Language>;
    meta: LanguagesListMeta;
}

export interface LanguagesListMeta {
    limit: number;
    skip: number;
    count: number;
}

@Injectable({
    providedIn: 'root',
})
export class LanguagesService {
    constructor(private http: HttpClient) {}

    fetch(skip: number = 0, limit: number = 500) {
        let params = {skip: skip.toString(), limit: limit.toString()};
        let url = getAPIRoot() + '/languages/';
        return this.http.get<LanguagesListResponseData>(url, {params: params});
    }
}


