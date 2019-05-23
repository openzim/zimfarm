import { NgModule } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Routes, RouterModule } from '@angular/router';
import { FormsModule, ReactiveFormsModule } from '@angular/forms';
import { AgGridModule } from 'ag-grid-angular';

import { SharedModule } from '../shared/shared.module';
import { ScheduleGridComponent } from './schedule-grid/schedule-grid.component';
import { CategoryFilterComponent } from './schedule-filters/category-filter';
import { LanguageFilterComponent } from './schedule-filters/language-filter';
import { QueueFilterComponent } from './schedule-filters/queue-filter';
import { NameFilterComponent } from './schedule-filters/name-filter';
import { TagsFilterComponent } from './schedule-filters/tags-filter';

const routes: Routes = [
    {
        path: '', 
        component: ScheduleGridComponent, 
        // children: [
        //     {path: ':name', component: ScheduleDetailComponent}
        // ]
    }
];

@NgModule({
    imports: [
        CommonModule,
        SharedModule,
        FormsModule,
        ReactiveFormsModule,
        RouterModule.forChild(routes),
        AgGridModule.withComponents([CategoryFilterComponent, LanguageFilterComponent,
                                     QueueFilterComponent, NameFilterComponent,
                                     TagsFilterComponent])
    ],
    declarations: [
        ScheduleGridComponent,
        CategoryFilterComponent,
        LanguageFilterComponent,
        QueueFilterComponent,
        NameFilterComponent,
        TagsFilterComponent]
})
export class ScheduleModule { }
