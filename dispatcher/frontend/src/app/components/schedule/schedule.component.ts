import { Component, OnInit } from '@angular/core';
import { Router } from '@angular/router';

import { SchedulesService, SchedulesListResponseData, SchedulesListMeta, Schedule } from '../../services/schedules.service';

@Component({
    templateUrl: './schedule.component.html',
    styleUrls: ['./schedule.component.css']
})
export class ScheduleComponent implements OnInit {
    constructor(private router: Router, private schedulesService: SchedulesService) {}

    public schedules: Array<Schedule> = []
    private meta: SchedulesListMeta;

    ngOnInit() {
        this.schedulesService.list().subscribe(data => {
            this.schedules = data.items
            this.meta = data.meta
        })
    }

    goPrevious(): void {
        let skip = Math.max(0, this.meta.skip - 20);
        this.schedulesService.list(skip, 20).subscribe(data => {
            this.schedules = data.items
            this.meta = data.meta
        })
    }

    goNext(): void {
        this.schedulesService.list(this.meta.skip + 20, 20).subscribe(data => {
            this.schedules = data.items
            this.meta = data.meta
        })
    }
}