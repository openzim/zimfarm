import { Component, OnInit } from '@angular/core';
import { ActivatedRoute } from '@angular/router';

@Component({
    templateUrl: './schedule-detail.component.html',
    styleUrls: ['./schedule-detail.component.css']
})
export class ScheduleDetailComponent implements OnInit {
    constructor(private route: ActivatedRoute) { }

    name: string;

    ngOnInit() {
        this.name = this.route.snapshot.paramMap.get('name')
    }

}

