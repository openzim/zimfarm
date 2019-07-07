import { Component, OnInit } from '@angular/core';
import { FormBuilder, FormGroup, FormControl } from '@angular/forms';
import { Router } from '@angular/router';
import { debounceTime, distinctUntilChanged, switchMap } from 'rxjs/operators';
import { Schedule, SchedulesService, SchedulesListRequestParams } from 'src/app/services/schedules.service';

import { LanguagesService } from '../../services/languages.service';
import { ConfigService, Category } from 'src/app/services/config.service';

@Component({
    templateUrl: './schedule-list.html',
    styleUrls: ['./schedule-list.css']
})
export class ScheduleListComponent implements OnInit {
    schedules: Schedule[] = []
    categories: Category[] = []
    categoriesFilterExpanded = true
    filterForm: FormGroup = new FormGroup({
        search: new FormControl(''),
        categories: new FormGroup({}),
        languages: new FormGroup({}),
    })

    constructor(
        private router: Router, 
        private configService: ConfigService,
        private languagesService: LanguagesService,
        private schedulesService: SchedulesService) {
            
        }

    ngOnInit() {
        this.initializeCategories(this.configService.categories);
        this.schedulesService.list(new SchedulesListRequestParams()).subscribe(data => {
            this.schedules = data.items;
        })
        this.filterForm.valueChanges.pipe(
            debounceTime(200),
            distinctUntilChanged(),
            switchMap(value => {
                let params = new SchedulesListRequestParams(200, 0, value)
                return this.schedulesService.list(params)
            })
        ).subscribe(data => {
            this.schedules = data.items;
        })
    }

    private initializeCategories(categories: Category[]) {
        this.filterForm.setControl('categories', categories.reduce((formGroup, category) => {
            formGroup.addControl(category.code, new FormControl(false))
            return formGroup
        }, new FormGroup({})))
        this.categories = categories
    }

    clearSearchText() {
        this.filterForm.controls['search'].setValue('')
    }

    scheduleListScrollIndexChange(event) {

    }

    toggleCategoriesFilter() {
        this.categoriesFilterExpanded = !this.categoriesFilterExpanded
    }
}