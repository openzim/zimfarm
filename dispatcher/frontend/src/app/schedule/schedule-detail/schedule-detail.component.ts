import { Component, OnInit } from '@angular/core';
import { ActivatedRoute } from '@angular/router';

import { SchedulesService, Schedule } from '../../services/schedules.service';

@Component({
    templateUrl: './schedule-detail.component.html',
    styleUrls: ['./schedule-detail.component.css']
})
export class ScheduleDetailComponent implements OnInit {
    constructor(private route: ActivatedRoute, private schedulesService: SchedulesService) { }

    public schedule: Schedule;

    ngOnInit() {
        let name = this.route.snapshot.paramMap.get('name');
        this.schedulesService.get(name).subscribe(data => {
            this.schedule = data;
            console.log(this.schedule.config.offliner);
        })
    }
}

