import { Component, OnInit } from '@angular/core';
import { IDatasource, IGetRowsParams } from 'ag-grid-community';

import { SchedulesService, Schedule } from '../../services/schedules.service';

@Component({
    templateUrl: './schedule-grid.component.html'
})
export class ScheduleGridComponent implements OnInit {
    constructor(private schedulesService: SchedulesService) { }

    public schedule: Schedule;

    ngOnInit() {
    }

    gridOptions = {
        rowModelType: 'infinite',
        datasource: new DataSource(this.schedulesService)
    };

    columnDefs = [
        {headerName: 'Name', field: 'name'},
        {headerName: 'Category', field: 'category', filter: true},
        {headerName: 'Language', field: 'language.name_en'},
        {headerName: 'Queue', field: 'config.queue'}
    ];
}

class DataSource implements IDatasource {
    constructor(private schedulesService: SchedulesService) { }

    getRows(params: IGetRowsParams): void {
        let skip = params.startRow;
        let limit = params.endRow - params.startRow;
        this.schedulesService.list(skip, limit).subscribe(data => {
            if (limit > data.items.length) {
                params.successCallback(data.items, params.startRow + data.items.length);
            } else {
                params.successCallback(data.items);
            }
        })
    }
}

