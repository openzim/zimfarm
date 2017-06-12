import { Component, OnInit } from '@angular/core';
import { Subscription }   from 'rxjs/Subscription';

import { AuthService } from '../service/auth.service';

import {NgbModule} from '@ng-bootstrap/ng-bootstrap';

@Component({
    selector: 'navigation-bar',
    templateUrl: './navigation-bar.component.html'
})
export class NavigationBarComponent {
    private scopeSubscription: Subscription;
    tabs: any[] = [];

    constructor(private authService: AuthService) {
        this.configureTabs(authService.scope);
        this.scopeSubscription = authService.scopeChange.subscribe(scope => {
            this.configureTabs(scope);
        })
    }

    configureTabs(scopes: string[]) {
        this.tabs = [];
        for (let scope of scopes) {
            if (scope == 'dashboard') {
                this.tabs.push({name: "Dashboard", routerLink: "dashboard"});
            } else if (scope == 'tasks') {
                this.tabs.push({name: "Tasks", routerLink: "tasks"});
            }
        }
    }

    ngOnDestroy() {
        this.scopeSubscription.unsubscribe();
    }
}