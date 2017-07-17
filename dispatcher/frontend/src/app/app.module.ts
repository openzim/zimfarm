import { NgModule } from '@angular/core';
import { BrowserModule } from '@angular/platform-browser';
import { HttpModule } from '@angular/http';
import { FormsModule }   from '@angular/forms';
import { NgbModule } from '@ng-bootstrap/ng-bootstrap';

import { AppComponent } from './app.component';
import { AppRoutingModule } from './app-routing.module';

import { AuthGuard } from './guard/auth.guard';

import { AuthService } from './service/auth.service';
import { TaskService } from './service/task.service';

import { LoginComponent } from './login/login.component';
import { NavigationBarComponent } from './navigation-bar/navigation-bar.component'
import { DashboardModule } from './dashboard/dashboard.module';
import { TasksModule } from './tasks/tasks.module';


@NgModule({
    imports: [ 
        BrowserModule, 
        HttpModule,
        FormsModule,
        NgbModule.forRoot(),
        DashboardModule,
        TasksModule,
        AppRoutingModule,
    ],
    declarations: [ 
        AppComponent, 
        LoginComponent,
        NavigationBarComponent
    ],
    providers: [
        AuthService,
        AuthGuard,
        TaskService
    ],
    bootstrap: [ AppComponent ]
})
export class AppModule { }
