import { HttpClient } from '@angular/common/http';
import { Injectable } from '@angular/core';

import { BaseService } from './base.service';

export interface Language {
    code: string;
    name_en: string;
    name_native: string;
}

export interface LanguagesListMeta {
    limit: number;
    skip: number;
    count: number;
}

export interface LanguagesListResponseData {
    items: Array<Language>;
    meta: LanguagesListMeta;
}

@Injectable({
    providedIn: 'root',
})
export class LanguagesService extends BaseService {
    languages: Array<Language> = []

    constructor(private http: HttpClient) {
        super();
        this.get().subscribe(data => {
            this.languages = data.items
        })
    }

    get(skip: number = 0, limit: number = 500) {
        let params = {skip: skip.toString(), limit: limit.toString()};
        let url = this.getAPIRoot() + '/languages/';
        return this.http.get<LanguagesListResponseData>(url, {params: params});
    }
}
