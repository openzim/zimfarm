import { Component, OnInit } from '@angular/core';
import { formatDate } from '@angular/common';
import { IDatasource, IGetRowsParams, GridOptions } from 'ag-grid-community';

import { SchedulesService, Schedule } from '../../services/schedules.service';
import { CategoryFilterComponent } from '../schedule-filters/category-filter';
import { LanguageFilterComponent } from '../schedule-filters/language-filter';
import { QueueFilterComponent } from '../schedule-filters/queue-filter';
import { NameFilterComponent } from '../schedule-filters/name-filter';
import { TagsFilterComponent } from '../schedule-filters/tags-filter';
import { LanguagesService } from '../../services/languages.service';

@Component({
    templateUrl: './schedule-grid.component.html'
})
export class ScheduleGridComponent implements OnInit {
    constructor(private schedulesService: SchedulesService,
                private languagesService: LanguagesService) { }

    public schedule: Schedule;

    ngOnInit() {
    }

    gridOptions: GridOptions = {
        rowModelType: 'infinite',
        datasource: new DataSource(this.schedulesService),
        frameworkComponents: {
            categoryFilter: CategoryFilterComponent,
            languageFilter: LanguageFilterComponent,
            queueFilter: QueueFilterComponent,
            nameFilter: NameFilterComponent,
            tagsFilter: TagsFilterComponent,
        },
        cacheBlockSize: 200,
        cacheOverflowSize: 20,
        onRowClicked: (event) => {
            let data = JSON.stringify(event.data, null, 2);
            let features = 'height=400,width=400,toolbar=0,menubar=0,location=0,resizable,scrollbars';
            var popup = window.open('about:blank', event.data.name, features);
            popup.document.write('<title>' + event.data.name + '</title><code><pre>' + data + '</pre></code>');
            if (window.focus) { popup.focus(); }
        }
    };

    columnDefs = [
        {headerName: 'Name', field: 'name', filter: 'nameFilter', width: 150, pinned: 'left'},
        {headerName: "Details", marryChildren: true, openByDefault: true, children: [
            {headerName: 'Queue', field: 'config.queue', filter: 'queueFilter', width: 120},
            {headerName: 'Language', field: 'language.code', filter: 'languageFilter', columnGroupShow: 'open', width: 150, cellRenderer: (params) => {return this.languagesService.getEnglishName(params.value);}},
            {headerName: 'Category', field: 'category', filter: 'categoryFilter', columnGroupShow: 'open', width: 120},
            {headerName: 'Tags', field: 'tags', filter: 'tagsFilter', columnGroupShow: 'open', width: 120}
        ]},
        {headerName: "Task this month", marryChildren: true, openByDefault: true, children: [
            {headerName: 'Status', field: 'task_this_month.status', width: 120},
            {headerName: 'Timestamp', field: 'task_this_month.updated_at', width: 120, cellRenderer: (params) => {
                if (params.value) {
                    return formatDate(params.value, 'MMM-dd HH:mm', 'en-US', '+0000');
                }
            }},
        ]},
        {headerName: "MWOffliner", marryChildren: true, openByDefault: true, children: [
            {headerName: 'mwUrl', field: 'config.flags.mwUrl', cellRenderer: (params) => {
                if (params.value) {
                    return `<a href="${params.value}">${params.value}</a>`;
                }
            }},
            {headerName: 'format', field: 'config.flags.format', columnGroupShow: 'open', width: 100,},
            {headerName: 'version', field: 'config.image.tag', columnGroupShow: 'open', width: 90,},
            {headerName: 'mainPage', field: 'config.flags.customMainPage', columnGroupShow: 'open', width: 100, resizable: true},
            {headerName: 'ns', field: 'config.flags.addNamespaces', columnGroupShow: 'open', width: 80,},
        ]}
    ];
}

class DataSource implements IDatasource {
    constructor(private schedulesService: SchedulesService) { }

    getRows(params: IGetRowsParams): void {
        let skip = params.startRow;
        let limit = params.endRow - params.startRow;
        let categories = params.filterModel['category'];
        let languages = params.filterModel['language.code'];
        let queues = params.filterModel['config.queue'];
        let name = params.filterModel['name'];
        let tags = params.filterModel['tags'];
        this.schedulesService.list(skip, limit, queues, categories, languages, name, tags).subscribe(data => {
            if (limit > data.items.length) {
                params.successCallback(data.items, params.startRow + data.items.length);
            } else {
                params.successCallback(data.items);
            }
        })
    }
}

