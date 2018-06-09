import { BrowserModule } from '@angular/platform-browser';
import { NgModule } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { HttpClientModule } from '@angular/common/http';
import { Routes, RouterModule } from '@angular/router';

import { RootComponent, AppComponent } from './components/components';
import { LoginComponent } from './components/login/login.component';
import { NavigationBarComponent } from './components/navigation-bar/navigation-bar.component';
import { QueueComponent } from './components/queue/queue.component';

import { AuthGuard } from './guards/auth.guard';

const routes: Routes = [
    {
        path: '',
        component: AppComponent,
        canActivate: [AuthGuard],
        children: [
            { path: 'queue', component: QueueComponent },
            { path: '**', redirectTo: 'queue' }
        ]
    },
    { path: 'login', component: LoginComponent },
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
    ],
    providers: [AuthGuard],
    bootstrap: [RootComponent]
})
export class AppModule { }
