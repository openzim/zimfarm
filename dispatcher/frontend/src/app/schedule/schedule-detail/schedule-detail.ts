import { Component, OnInit } from '@angular/core';
import { ActivatedRoute } from '@angular/router';
import { Observable } from 'rxjs';
import { switchMap } from 'rxjs/operators';
import { FormBuilder, FormGroup, FormControl } from '@angular/forms';


import { Schedule, SchedulesService } from '../../services/schedules.service';
import { categories } from '../../services/entities';

@Component({
    templateUrl: './schedule-detail.html',
    styleUrls: ['./schedule-detail.css']
})
export class ScheduleDetailComponent implements OnInit {
    name = new FormControl('');

    constructor(
        private route: ActivatedRoute, 
        private schedulesService: SchedulesService, 
        private formBuilder: FormBuilder) {
            this.scheduleForm = this.formBuilder.group({
                name: 'test',
                address: ''
            })
        }
    schedule$: Observable<Schedule>;
    categories = categories;
    scheduleForm: FormGroup;

    ngOnInit() {
        this.schedule$ = this.route.paramMap.pipe(
            switchMap(params => {
                return this.schedulesService.get(params.get('id_or_name'));
            })
        );
        // this.schedule$.subscribe(schedule => {
        //     this.scheduleForm = this.formBuilder.group(schedule);
        // })
    }

    onSubmit(schedule) {
        console.log('submit buttion is clicked.', schedule)
    }
}