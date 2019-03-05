import { Component, OnInit } from '@angular/core';
import { IDatasource, IGetRowsParams, GridOptions } from 'ag-grid-community';

import { SchedulesService, Schedule } from '../../services/schedules.service';
import { CategoryFilterComponent } from '../schedule-filters/category-filter';

@Component({
    templateUrl: './schedule-grid.component.html'
})
export class ScheduleGridComponent implements OnInit {
    constructor(private schedulesService: SchedulesService) { }

    public schedule: Schedule;

    ngOnInit() {
    }

    gridOptions: GridOptions = {
        rowModelType: 'infinite',
        datasource: new DataSource(this.schedulesService),
        frameworkComponents: {
            categoryFilter: CategoryFilterComponent
        }
    };

    columnDefs = [
        {headerName: 'Name', field: 'name', width: 150, pinned: 'left'},
        {headerName: "Details", marryChildren: true, openByDefault: true, children: [
            {headerName: 'Queue', field: 'config.queue', width: 120},
            {headerName: 'Language', field: 'language.name_en', columnGroupShow: 'open', width: 150, },
            {headerName: 'Category', field: 'category', filter: 'categoryFilter', columnGroupShow: 'open', width: 120, }
        ]},
        {headerName: "Task", marryChildren: true, openByDefault: true, children: [
            {headerName: 'Status', field: 'most_recent_task.status', width: 120},
        ]},
        {headerName: "MWOffliner", marryChildren: true, openByDefault: true, children: [
            {headerName: 'mwUrl', field: 'config.flags.mwUrl'},
            {headerName: 'format', field: 'config.flags.format', columnGroupShow: 'open', width: 100,},
            {headerName: 'version', field: 'config.image.tag', columnGroupShow: 'open', width: 100,},
            {headerName: 'namespaces', field: 'config.flags.addNamespaces', columnGroupShow: 'open', width: 120,},
            {headerName: 'customMainPage', field: 'config.flags.customMainPage', columnGroupShow: 'open', 
            width: 200, minWidth: 100, resizable: true},
        ]}
    ];
}

class DataSource implements IDatasource {
    constructor(private schedulesService: SchedulesService) { }

    getRows(params: IGetRowsParams): void {
        let skip = params.startRow;
        let limit = params.endRow - params.startRow;
        let categories = params.filterModel['category'];
        this.schedulesService.list(skip, limit, categories).subscribe(data => {
            if (limit > data.items.length) {
                params.successCallback(data.items, params.startRow + data.items.length);
            } else {
                params.successCallback(data.items);
            }
        })
    }
}

