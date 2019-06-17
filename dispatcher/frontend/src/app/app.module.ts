import { BrowserModule } from '@angular/platform-browser';
import { NgModule } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { HttpClientModule } from '@angular/common/http';
import { Routes, RouterModule } from '@angular/router';
import { HTTP_INTERCEPTORS } from '@angular/common/http';
import { BrowserAnimationsModule } from '@angular/platform-browser/animations';

import { RootComponent, AppComponent } from './components/components';
import { LoginComponent } from './components/login/login.component';
import { NavigationBarComponent } from './components/navigation-bar/navigation-bar.component';
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
            { path: 'schedules', loadChildren: () => import('./schedule/schedule.module').then(m => m.ScheduleModule) },
            { path: 'tasks', loadChildren: () => import('./task/task.module').then(m => m.TaskModule) },
            { path: 'user', component: UserComponent },
            { path: '**', redirectTo: 'schedules' }
        ]
    },
    
    { path: '', redirectTo: 'login', pathMatch: 'full' },
];

@NgModule({
    imports: [
        BrowserModule,
        FormsModule,
        HttpClientModule,
        BrowserAnimationsModule,
        RouterModule.forRoot(routes)
    ],
    declarations: [
        RootComponent,
        AppComponent,
        LoginComponent,
        NavigationBarComponent,
        UserComponent
    ],
    providers: [
        AuthGuard,
        [{ provide: HTTP_INTERCEPTORS, useClass: AccessTokenInterceptor, multi: true }]
    ],
    bootstrap: [RootComponent]
})
export class AppModule { }
