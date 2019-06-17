import { CommonModule } from '@angular/common';
import { NgModule } from '@angular/core';
import { FormsModule, ReactiveFormsModule } from '@angular/forms';
import { MatButtonModule } from '@angular/material/button';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatInputModule } from '@angular/material/input';
import { MatListModule } from '@angular/material/list';
import { MatSelectModule } from '@angular/material/select';
import { MatSidenavModule } from '@angular/material/sidenav';
import { MatToolbarModule } from '@angular/material/toolbar';
import { RouterModule, Routes } from '@angular/router';
import { ScrollingModule } from '@angular/cdk/scrolling';
import {MatCardModule} from '@angular/material/card'; 

import { SharedModule } from '../shared/shared.module';
import { ScheduleDetailComponent } from './schedule-detail/schedule-detail';
import { ScheduleListItemComponent } from './schedule-list-item/schedule-list-item';
import { ScheduleListComponent } from './schedule-list/schedule-list';


const routes: Routes = [
    {
        path: '', 
        component: ScheduleListComponent, 
        children: [
            {path: ':id_or_name', component: ScheduleDetailComponent}
        ]
    }
];

@NgModule({
    imports: [
        CommonModule,
        SharedModule,
        FormsModule,
        ReactiveFormsModule,
        RouterModule.forChild(routes),
        ScrollingModule,
        MatSidenavModule,
        MatFormFieldModule,
        MatInputModule,
        MatSelectModule,
        MatButtonModule,
        MatToolbarModule,
        MatListModule,
        MatCardModule,
    ],
    declarations: [
        ScheduleListComponent,
        ScheduleListItemComponent,
        ScheduleDetailComponent]
})
export class ScheduleModule { }
