import { NgModule } from '@angular/core';
import { BrowserModule } from '@angular/platform-browser';

import { AppComponent } from './app.component';
import { AppRoutingModule }     from './app-routing.module';
import { DashboardComponent } from './Dashboard/dashboard.component';
import { TasksComponent } from './Tasks/tasks.component';
import { TemplatesComponent } from './Templates/templates.component';
import { NodesComponent } from './Nodes/nodes.component';


@NgModule({
    imports: [ BrowserModule, AppRoutingModule ],
    declarations: [ 
        AppComponent, 
        DashboardComponent, 
        TasksComponent, 
        TemplatesComponent,
        NodesComponent
    ],
    bootstrap: [ AppComponent ]
})
export class AppModule { }
