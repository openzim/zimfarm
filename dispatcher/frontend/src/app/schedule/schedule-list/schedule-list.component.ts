import { Component, OnInit } from '@angular/core';
import { Router, ActivatedRoute } from '@angular/router';
import { switchMap, map } from 'rxjs/operators';

import { SchedulesService, SchedulesListResponseData, SchedulesListMeta, Schedule } from '../../services/schedules.service';

@Component({
    templateUrl: './schedule-list.component.html',
    styleUrls: ['./schedule-list.component.css']
})
export class ScheduleListComponent implements OnInit {
    constructor(private router: Router, private route: ActivatedRoute, private schedulesService: SchedulesService) {}

    public schedules: Array<Schedule> = []
    private selectedScheduleName: string | null;
    private meta: SchedulesListMeta;

    ngOnInit() {
        this.schedulesService.list(0, 200).subscribe(data => {
            this.schedules = data.items;
            this.meta = data.meta;

            let firstChild = this.route.snapshot.firstChild;
            if (firstChild != null) {
                this.selectedScheduleName = firstChild.url[0].path;
            }
        })
    }

    onSelect(schedule: Schedule): void {
        if (this.isSelected(schedule)) {
            this.selectedScheduleName = null;
            this.router.navigate(['../'], {relativeTo: this.route});
        } else {
            this.selectedScheduleName = schedule.name;
            this.router.navigate([schedule.name], {relativeTo: this.route});
        }
    }

    isSelected(schedule: Schedule): boolean {
        if (this.selectedScheduleName == null) { return false; }
        return this.selectedScheduleName == schedule.name;
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
