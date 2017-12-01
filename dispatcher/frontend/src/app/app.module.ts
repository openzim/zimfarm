import { BrowserModule } from '@angular/platform-browser';
import { NgModule } from '@angular/core';
import { HttpClientModule } from '@angular/common/http';
import { FormsModule } from '@angular/forms';

import { AppComponent } from './root/app.component';
import { NavigationComponent } from './navigation/navigation.component';

import { RoutingModule } from './routing.module';


@NgModule({
    declarations: [
        AppComponent,
        NavigationComponent
    ],
    imports: [
        BrowserModule,
        HttpClientModule,
        RoutingModule
    ],
    providers: [],
    bootstrap: [AppComponent]
})
export class AppModule { }
