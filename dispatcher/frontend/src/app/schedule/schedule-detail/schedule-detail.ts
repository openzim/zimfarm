import { Component, OnInit } from '@angular/core';
import { ActivatedRoute } from '@angular/router';
import { Observable, scheduled } from 'rxjs';
import { switchMap } from 'rxjs/operators';
import { FormBuilder, FormGroup, FormControl } from '@angular/forms';


import { Schedule, SchedulesService } from '../../services/schedules.service';
import { categories } from '../../services/entities';

@Component({
    templateUrl: './schedule-detail.html',
    styleUrls: ['./schedule-detail.css']
})
export class ScheduleDetailComponent implements OnInit {
    schedule$: Observable<Schedule>;
    offlinerConfigForm = new FormGroup({
        image: new FormGroup({
            name: new FormControl(''),
            tag: new FormControl('')
        }),
        flags: new FormGroup({
            mwUrl: new FormControl(''),
            adminEmail: new FormControl(''),
            customMainPage: new FormControl('')
        })
    });

    constructor(
        private route: ActivatedRoute, 
        private schedulesService: SchedulesService, 
        private formBuilder: FormBuilder) {}

    ngOnInit() {
        this.schedule$ = this.route.paramMap.pipe(
            switchMap(params => {
                return this.schedulesService.get(params.get('id_or_name'));
            })
        );
        this.schedule$.subscribe(schedule => {
            this.offlinerConfigForm.patchValue(schedule.config);
        })
    }

    onSubmit(schedule) {
        console.log('submit buttion is clicked.', schedule)
    }
}