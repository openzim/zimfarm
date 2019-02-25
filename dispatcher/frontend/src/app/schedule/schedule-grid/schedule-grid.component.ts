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
        {headerName: "Details", marryChildren: true, children: [
            {headerName: 'Name', field: 'name'},
            {headerName: 'Language', field: 'language.name_en', width: 150},
            {headerName: 'Category', field: 'category', filter: 'categoryFilter', width: 120},
            {headerName: 'Queue', field: 'config.queue', width: 120}
        ]},
        {headerName: "MWOffliner", marryChildren: true, children: [
            {headerName: 'mwUrl', field: 'config.flags.mwUrl'},
            {headerName: 'format', field: 'config.flags.format', width: 100},
            {headerName: 'version', field: 'config.image.tag', width: 100},
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

