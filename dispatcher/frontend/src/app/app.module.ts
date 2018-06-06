import { BrowserModule } from '@angular/platform-browser';
import { NgModule } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { HttpClientModule } from '@angular/common/http';
import { Routes, RouterModule } from '@angular/router';

import { RootComponent } from './root.component';
import { LoginComponent } from './login/login.component';
import { QueueComponent } from './queue/queue.component';

import { AuthGuard } from './guards/auth.guard';

const routes: Routes = [
    { path: '', redirectTo: 'queue', pathMatch: 'full' },
    { path: 'login', component: LoginComponent },
    { path: 'queue', component: QueueComponent, canActivate: [AuthGuard] },
    { path: '**', redirectTo: '' }
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
        QueueComponent,
        LoginComponent
    ],
    providers: [AuthGuard],
    bootstrap: [RootComponent]
})
export class AppModule { }
