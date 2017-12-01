import { NgModule } from '@angular/core';
import { CommonModule } from '@angular/common';

import { RoutingModule } from './routing.module';
import { DashboardComponent } from './dashboard.component';

import { TaskService } from '../service/task.service';


@NgModule({
    imports: [
        CommonModule,
        RoutingModule
    ],
    declarations: [
        DashboardComponent
    ],
    providers: [TaskService]
})
export class DashboardModule { }