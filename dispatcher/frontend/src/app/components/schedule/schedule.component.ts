import { Component, OnInit } from '@angular/core';
import { Router } from '@angular/router';

import { SchedulesService } from '../../services/schedules.service';

@Component({
    templateUrl: './schedule.component.html',
})
export class ScheduleComponent implements OnInit {
    constructor(private router: Router, private schedulesService: SchedulesService) {}

    ngOnInit() {
        this.schedulesService.list().subscribe(data => {
            console.log(data)
        })
    }
}