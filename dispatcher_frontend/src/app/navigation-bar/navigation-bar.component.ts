import { Component, OnInit } from '@angular/core';

import { AuthService } from '../service/auth.service';

@Component({
    selector: 'navigation-bar',
    templateUrl: 'app/navigation-bar/navigation-bar.component.html'
})
export class NavigationBarComponent {

    constructor(
        private authService: AuthService
    ){}

    tabs = [
        {name: "Dashboard", routerLink: "dashboard"},
        {name: "Tasks", routerLink: "tasks"},
        {name: "Nodes", routerLink: "nodes"}
    ]

    ngOnInit() {
    }
}