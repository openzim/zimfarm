import { NgModule } from '@angular/core';
import { BrowserModule } from '@angular/platform-browser';
import { HttpModule } from '@angular/http';

import { AppComponent } from './app.component';
import { AppRoutingModule } from './app-routing.module';
import { DashboardComponent } from './Dashboard/dashboard.component';
import { TasksComponent } from './Tasks/tasks.component';
import { TemplatesComponent } from './Templates/templates.component';
import { NodesComponent } from './Nodes/nodes.component';
import { TaskService } from './model/task.service';


@NgModule({
    imports: [ 
        BrowserModule, 
        AppRoutingModule,
        HttpModule
    ],
    declarations: [ 
        AppComponent, 
        DashboardComponent, 
        TasksComponent, 
        TemplatesComponent,
        NodesComponent
    ],
    providers: [ TaskService ],
    bootstrap: [ AppComponent ]
})
export class AppModule { }
