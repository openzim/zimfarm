import { BrowserModule } from '@angular/platform-browser';
import { NgModule } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { HttpClientModule } from '@angular/common/http';
import { Routes, RouterModule } from '@angular/router';
import { HTTP_INTERCEPTORS } from '@angular/common/http';

import { TimeAgoPipe } from 'time-ago-pipe';

import { RootComponent, AppComponent } from './components/components';
import { LoginComponent } from './components/login/login.component';
import { NavigationBarComponent } from './components/navigation-bar/navigation-bar.component';
import { QueueComponent } from './components/queue/queue.component';
import { ScheduleComponent } from './components/schedule/schedule.component';
import { WorkerComponent } from './components/worker/worker.component';
import { LogComponent } from './components/log/log.component';
import { UserComponent } from './components/user/user.component';

import { AuthGuard } from './guards/auth.guard';
import { AccessTokenInterceptor } from './services/auth.service';

const routes: Routes = [
    { path: 'login', component: LoginComponent },
    {
        path: '',
        component: AppComponent,
        canActivate: [AuthGuard],
        children: [
            { path: 'queue', component: QueueComponent },
            { path: 'schedule', component: ScheduleComponent },
            { path: 'worker', component: WorkerComponent },
            { path: 'log', component: LogComponent },
            { path: 'user', component: UserComponent },
            { path: '**', redirectTo: 'queue' }
        ]
    },
    
    { path: '', redirectTo: 'login', pathMatch: 'full' },
];

@NgModule({
    imports: [
        BrowserModule,
        FormsModule,
        HttpClientModule,
        RouterModule.forRoot(routes)
    ],
    declarations: [
        TimeAgoPipe,
        RootComponent,
        AppComponent,
        LoginComponent,
        NavigationBarComponent,
        QueueComponent,
        ScheduleComponent,
        WorkerComponent,
        LogComponent,
        UserComponent
    ],
    providers: [
        AuthGuard,
        [{ provide: HTTP_INTERCEPTORS, useClass: AccessTokenInterceptor, multi: true }]
    ],
    bootstrap: [RootComponent]
})
export class AppModule { }
