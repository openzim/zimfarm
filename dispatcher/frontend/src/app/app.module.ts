import { BrowserModule } from '@angular/platform-browser';
import { NgModule } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { HttpClientModule } from '@angular/common/http';
import { Routes, RouterModule } from '@angular/router';

import { RootComponent } from './components/root.component';
import { LoginComponent } from './components/login/login.component';
import { NavigationBarComponent } from './components/navigation-bar/navigation-bar.component';
import { QueueComponent } from './components/queue/queue.component';

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
        LoginComponent,
        NavigationBarComponent,
        QueueComponent,
    ],
    providers: [AuthGuard],
    bootstrap: [RootComponent]
})
export class AppModule { }
