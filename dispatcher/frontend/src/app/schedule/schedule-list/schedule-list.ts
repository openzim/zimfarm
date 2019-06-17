import { Component, OnInit } from '@angular/core';
import { FormBuilder, FormGroup } from '@angular/forms';
import { Router } from '@angular/router';
import { debounceTime, distinctUntilChanged, switchMap } from 'rxjs/operators';
import { Schedule, SchedulesService, SchedulesListRequestParams } from 'src/app/services/schedules.service';

import { LanguagesService } from '../../services/languages.service';

@Component({
    templateUrl: './schedule-list.html',
    styleUrls: ['./schedule-list.css']
})
export class ScheduleListComponent implements OnInit {
    scheduleFilterForm: FormGroup;
    schedules: Array<Schedule> = []

    constructor(
        private router: Router, 
        private languagesService: LanguagesService,
        private schedulesService: SchedulesService, 
        private formBuilder: FormBuilder) {
            this.scheduleFilterForm = this.formBuilder.group({
                name: '',
            })
        }

    ngOnInit() {
        this.schedulesService.list(new SchedulesListRequestParams()).subscribe(data => {
            this.schedules = data.items;
        })
        this.scheduleFilterForm.valueChanges.pipe(
            debounceTime(200),
            distinctUntilChanged(),
            switchMap(value => {
                let params = new SchedulesListRequestParams()
                params.name = value['name']
                return this.schedulesService.list(params)
            })
        ).subscribe(data => {
            this.schedules = data.items;
        })
    }

    clearSearchText() {
        this.scheduleFilterForm.controls['name'].setValue('')
    }

    scheduleListScrollIndexChange(event) {

    }
}