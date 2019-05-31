import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';

import { getAPIRoot } from './config';

export interface TagsListResponseData {
    items: Array<string>;
    meta: TagsListMeta;
}

export interface TagsListMeta {
    limit: number;
    skip: number;
    count: number;
}

@Injectable({
    providedIn: 'root',
})
export class TagsService {
    constructor(private http: HttpClient) {}

    fetch(skip: number = 0, limit: number = 500) {
        let params = {skip: skip.toString(), limit: limit.toString()};
        let url = getAPIRoot() + '/tags/';
        return this.http.get<TagsListResponseData>(url, {params: params});
    }
}


