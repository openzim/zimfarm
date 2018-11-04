import { BrowserModule } from '@angular/platform-browser';
import { NgModule } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { HttpClientModule } from '@angular/common/http';
import { Routes, RouterModule } from '@angular/router';
import { HTTP_INTERCEPTORS } from '@angular/common/http';

import { RootComponent, AppComponent } from './components/components';
import { LoginComponent } from './components/login/login.component';
import { NavigationBarComponent } from './components/navigation-bar/navigation-bar.component';
import { QueueComponent } from './components/queue/queue.component';
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
            { path: 'schedule', loadChildren: './schedule/schedule.module#ScheduleModule' },
            { path: 'queue', component: QueueComponent },
            { path: 'worker', component: WorkerComponent },
            { path: 'log', component: LogComponent },
            { path: 'user', component: UserComponent },
            { path: '**', redirectTo: 'schedule' }
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
        RootComponent,
        AppComponent,
        LoginComponent,
        NavigationBarComponent,
        QueueComponent,
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
