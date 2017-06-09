import { Component, OnInit } from '@angular/core';

@Component({
    selector: 'navigation-bar',
    templateUrl: 'app/navigation-bar/navigation-bar.component.html'
})
export class NavigationBarComponent {
    tabs = [
        {name: "Dashboard", routerLink: "dashboard"},
        {name: "Tasks", routerLink: "tasks"},
        {name: "Nodes", routerLink: "nodes"}
    ]
    
    ngOnInit() {
    }
}