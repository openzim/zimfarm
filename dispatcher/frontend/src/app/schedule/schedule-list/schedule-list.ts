import { Component, OnInit } from '@angular/core';
import { Router } from '@angular/router';

import { LanguagesService } from '../../services/languages.service';
import { FormBuilder, FormGroup } from '@angular/forms';
import { SchedulesService, Schedule } from 'src/app/services/schedules.service';
import { switchMap } from 'rxjs/operators';

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
        this.schedulesService.list('').subscribe(data => {
            this.schedules = data.items;
        })
        this.scheduleFilterForm.valueChanges.subscribe(value => {
            this.schedulesService.list(value['name']).subscribe(data => {
                this.schedules = data.items;
            })
        })
    }
}