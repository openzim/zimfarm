import { HttpClient } from '@angular/common/http';
import { Injectable } from '@angular/core';

import { BaseService } from './base.service';

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
export class TagsService extends BaseService{
    constructor(private http: HttpClient) { super() }

    fetch(skip: number = 0, limit: number = 500) {
        let params = {skip: skip.toString(), limit: limit.toString()};
        let url = this.getAPIRoot() + '/tags/';
        return this.http.get<TagsListResponseData>(url, {params: params});
    }
}


