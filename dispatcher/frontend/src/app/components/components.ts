import { Component } from '@angular/core';

@Component({
  selector: 'root',
  template: '<router-outlet></router-outlet>'
})
export class RootComponent {}

@Component({
  template: '<navigation-bar></navigation-bar><router-outlet></router-outlet>'
})
export class AppComponent {}