import { Component, OnInit } from '@angular/core';
import { Subscription }   from 'rxjs/Subscription';
import { NgbModule } from '@ng-bootstrap/ng-bootstrap';

import { AuthService } from '../service/auth.service';
import { User } from '../model/user';


@Component({
    selector: 'navigation-bar',
    templateUrl: './navigation-bar.component.html',
    styleUrls: ['./navigation-bar.component.css']
})
export class NavigationBarComponent {
    private userSubscription: Subscription;
    tabs: any[] = [];

    constructor(public authService: AuthService) {
        this.configureTabs(authService.user)
        this.userSubscription = authService.userChanged.subscribe(user => {
            this.configureTabs(user)
        })
    }

    configureTabs(user: User) {
        if (user == null) {
            this.tabs = []
        } else {
            this.tabs = [{name: "Tasks", routerLink: "tasks"}]
        }
        
        // TODO: dynamically generate configuration for tabs based on scope of user
        // for (let scope of scopes) {
        //     if (scope == 'dashboard') {
        //         this.tabs.push({name: "Dashboard", routerLink: "dashboard"});
        //     } else if (scope == 'tasks') {
        //         this.tabs.push({name: "Tasks", routerLink: "tasks"});
        //     }
        // }
    }

    ngOnDestroy() {
        this.userSubscription.unsubscribe();
    }
}