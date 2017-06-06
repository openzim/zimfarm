import { NgModule } from '@angular/core';
import { BrowserModule } from '@angular/platform-browser';
import { HttpModule } from '@angular/http';
import { FormsModule }   from '@angular/forms';
import { NgbModule } from '@ng-bootstrap/ng-bootstrap';

import { AppComponent } from './app.component';
import { AppRoutingModule } from './app-routing.module';

import { AuthGuard } from './guard/auth.guard';

import { LoginComponent } from './login/login.component';
import { DashboardModule } from './dashboard/dashboard.module';
import { TasksComponent } from './Tasks/tasks.component';
import { TaskDetailComponent } from './Tasks/task-detail.component';
import { NodesComponent } from './nodes/nodes.component';
import { TaskService } from './model/task.service';


@NgModule({
    imports: [ 
        BrowserModule, 
        AppRoutingModule,
        HttpModule,
        FormsModule,
        NgbModule.forRoot(),
        DashboardModule
    ],
    declarations: [ 
        AppComponent, 
        LoginComponent,
        TasksComponent, 
        TaskDetailComponent,
        NodesComponent
    ],
    providers: [
        AuthGuard,
        TaskService
    ],
    bootstrap: [ AppComponent ]
})
export class AppModule { }
