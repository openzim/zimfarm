(window["webpackJsonp"] = window["webpackJsonp"] || []).push([["main"],{

/***/ "./src/$$_lazy_route_resource lazy recursive":
/*!**********************************************************!*\
  !*** ./src/$$_lazy_route_resource lazy namespace object ***!
  \**********************************************************/
/*! no static exports found */
/***/ (function(module, exports, __webpack_require__) {

var map = {
	"./schedule/schedule.module": [
		"./src/app/schedule/schedule.module.ts",
		"schedule-schedule-module"
	]
};
function webpackAsyncContext(req) {
	var ids = map[req];
	if(!ids) {
		return Promise.resolve().then(function() {
			var e = new Error("Cannot find module '" + req + "'");
			e.code = 'MODULE_NOT_FOUND';
			throw e;
		});
	}
	return __webpack_require__.e(ids[1]).then(function() {
		var id = ids[0];
		return __webpack_require__(id);
	});
}
webpackAsyncContext.keys = function webpackAsyncContextKeys() {
	return Object.keys(map);
};
webpackAsyncContext.id = "./src/$$_lazy_route_resource lazy recursive";
module.exports = webpackAsyncContext;

/***/ }),

/***/ "./src/app/app.module.ts":
/*!*******************************!*\
  !*** ./src/app/app.module.ts ***!
  \*******************************/
/*! exports provided: AppModule */
/***/ (function(module, __webpack_exports__, __webpack_require__) {

"use strict";
__webpack_require__.r(__webpack_exports__);
/* harmony export (binding) */ __webpack_require__.d(__webpack_exports__, "AppModule", function() { return AppModule; });
/* harmony import */ var _angular_platform_browser__WEBPACK_IMPORTED_MODULE_0__ = __webpack_require__(/*! @angular/platform-browser */ "./node_modules/@angular/platform-browser/fesm5/platform-browser.js");
/* harmony import */ var _angular_core__WEBPACK_IMPORTED_MODULE_1__ = __webpack_require__(/*! @angular/core */ "./node_modules/@angular/core/fesm5/core.js");
/* harmony import */ var _angular_forms__WEBPACK_IMPORTED_MODULE_2__ = __webpack_require__(/*! @angular/forms */ "./node_modules/@angular/forms/fesm5/forms.js");
/* harmony import */ var _angular_common_http__WEBPACK_IMPORTED_MODULE_3__ = __webpack_require__(/*! @angular/common/http */ "./node_modules/@angular/common/fesm5/http.js");
/* harmony import */ var _angular_router__WEBPACK_IMPORTED_MODULE_4__ = __webpack_require__(/*! @angular/router */ "./node_modules/@angular/router/fesm5/router.js");
/* harmony import */ var _components_components__WEBPACK_IMPORTED_MODULE_5__ = __webpack_require__(/*! ./components/components */ "./src/app/components/components.ts");
/* harmony import */ var _components_login_login_component__WEBPACK_IMPORTED_MODULE_6__ = __webpack_require__(/*! ./components/login/login.component */ "./src/app/components/login/login.component.ts");
/* harmony import */ var _components_navigation_bar_navigation_bar_component__WEBPACK_IMPORTED_MODULE_7__ = __webpack_require__(/*! ./components/navigation-bar/navigation-bar.component */ "./src/app/components/navigation-bar/navigation-bar.component.ts");
/* harmony import */ var _components_queue_queue_component__WEBPACK_IMPORTED_MODULE_8__ = __webpack_require__(/*! ./components/queue/queue.component */ "./src/app/components/queue/queue.component.ts");
/* harmony import */ var _components_worker_worker_component__WEBPACK_IMPORTED_MODULE_9__ = __webpack_require__(/*! ./components/worker/worker.component */ "./src/app/components/worker/worker.component.ts");
/* harmony import */ var _components_log_log_component__WEBPACK_IMPORTED_MODULE_10__ = __webpack_require__(/*! ./components/log/log.component */ "./src/app/components/log/log.component.ts");
/* harmony import */ var _components_user_user_component__WEBPACK_IMPORTED_MODULE_11__ = __webpack_require__(/*! ./components/user/user.component */ "./src/app/components/user/user.component.ts");
/* harmony import */ var _guards_auth_guard__WEBPACK_IMPORTED_MODULE_12__ = __webpack_require__(/*! ./guards/auth.guard */ "./src/app/guards/auth.guard.ts");
/* harmony import */ var _services_auth_service__WEBPACK_IMPORTED_MODULE_13__ = __webpack_require__(/*! ./services/auth.service */ "./src/app/services/auth.service.ts");
var __decorate = (undefined && undefined.__decorate) || function (decorators, target, key, desc) {
    var c = arguments.length, r = c < 3 ? target : desc === null ? desc = Object.getOwnPropertyDescriptor(target, key) : desc, d;
    if (typeof Reflect === "object" && typeof Reflect.decorate === "function") r = Reflect.decorate(decorators, target, key, desc);
    else for (var i = decorators.length - 1; i >= 0; i--) if (d = decorators[i]) r = (c < 3 ? d(r) : c > 3 ? d(target, key, r) : d(target, key)) || r;
    return c > 3 && r && Object.defineProperty(target, key, r), r;
};















var routes = [
    { path: 'login', component: _components_login_login_component__WEBPACK_IMPORTED_MODULE_6__["LoginComponent"] },
    {
        path: '',
        component: _components_components__WEBPACK_IMPORTED_MODULE_5__["AppComponent"],
        canActivate: [_guards_auth_guard__WEBPACK_IMPORTED_MODULE_12__["AuthGuard"]],
        children: [
            { path: 'schedule', loadChildren: './schedule/schedule.module#ScheduleModule' },
            { path: 'queue', component: _components_queue_queue_component__WEBPACK_IMPORTED_MODULE_8__["QueueComponent"] },
            { path: 'worker', component: _components_worker_worker_component__WEBPACK_IMPORTED_MODULE_9__["WorkerComponent"] },
            { path: 'log', component: _components_log_log_component__WEBPACK_IMPORTED_MODULE_10__["LogComponent"] },
            { path: 'user', component: _components_user_user_component__WEBPACK_IMPORTED_MODULE_11__["UserComponent"] },
            { path: '**', redirectTo: 'schedule' }
        ]
    },
    { path: '', redirectTo: 'login', pathMatch: 'full' },
];
var AppModule = /** @class */ (function () {
    function AppModule() {
    }
    AppModule = __decorate([
        Object(_angular_core__WEBPACK_IMPORTED_MODULE_1__["NgModule"])({
            imports: [
                _angular_platform_browser__WEBPACK_IMPORTED_MODULE_0__["BrowserModule"],
                _angular_forms__WEBPACK_IMPORTED_MODULE_2__["FormsModule"],
                _angular_common_http__WEBPACK_IMPORTED_MODULE_3__["HttpClientModule"],
                _angular_router__WEBPACK_IMPORTED_MODULE_4__["RouterModule"].forRoot(routes)
            ],
            declarations: [
                _components_components__WEBPACK_IMPORTED_MODULE_5__["RootComponent"],
                _components_components__WEBPACK_IMPORTED_MODULE_5__["AppComponent"],
                _components_login_login_component__WEBPACK_IMPORTED_MODULE_6__["LoginComponent"],
                _components_navigation_bar_navigation_bar_component__WEBPACK_IMPORTED_MODULE_7__["NavigationBarComponent"],
                _components_queue_queue_component__WEBPACK_IMPORTED_MODULE_8__["QueueComponent"],
                _components_worker_worker_component__WEBPACK_IMPORTED_MODULE_9__["WorkerComponent"],
                _components_log_log_component__WEBPACK_IMPORTED_MODULE_10__["LogComponent"],
                _components_user_user_component__WEBPACK_IMPORTED_MODULE_11__["UserComponent"]
            ],
            providers: [
                _guards_auth_guard__WEBPACK_IMPORTED_MODULE_12__["AuthGuard"],
                [{ provide: _angular_common_http__WEBPACK_IMPORTED_MODULE_3__["HTTP_INTERCEPTORS"], useClass: _services_auth_service__WEBPACK_IMPORTED_MODULE_13__["AccessTokenInterceptor"], multi: true }]
            ],
            bootstrap: [_components_components__WEBPACK_IMPORTED_MODULE_5__["RootComponent"]]
        })
    ], AppModule);
    return AppModule;
}());



/***/ }),

/***/ "./src/app/components/components.ts":
/*!******************************************!*\
  !*** ./src/app/components/components.ts ***!
  \******************************************/
/*! exports provided: RootComponent, AppComponent */
/***/ (function(module, __webpack_exports__, __webpack_require__) {

"use strict";
__webpack_require__.r(__webpack_exports__);
/* harmony export (binding) */ __webpack_require__.d(__webpack_exports__, "RootComponent", function() { return RootComponent; });
/* harmony export (binding) */ __webpack_require__.d(__webpack_exports__, "AppComponent", function() { return AppComponent; });
/* harmony import */ var _angular_core__WEBPACK_IMPORTED_MODULE_0__ = __webpack_require__(/*! @angular/core */ "./node_modules/@angular/core/fesm5/core.js");
var __decorate = (undefined && undefined.__decorate) || function (decorators, target, key, desc) {
    var c = arguments.length, r = c < 3 ? target : desc === null ? desc = Object.getOwnPropertyDescriptor(target, key) : desc, d;
    if (typeof Reflect === "object" && typeof Reflect.decorate === "function") r = Reflect.decorate(decorators, target, key, desc);
    else for (var i = decorators.length - 1; i >= 0; i--) if (d = decorators[i]) r = (c < 3 ? d(r) : c > 3 ? d(target, key, r) : d(target, key)) || r;
    return c > 3 && r && Object.defineProperty(target, key, r), r;
};

var RootComponent = /** @class */ (function () {
    function RootComponent() {
    }
    RootComponent = __decorate([
        Object(_angular_core__WEBPACK_IMPORTED_MODULE_0__["Component"])({
            selector: 'root',
            template: '<router-outlet></router-outlet>'
        })
    ], RootComponent);
    return RootComponent;
}());

var AppComponent = /** @class */ (function () {
    function AppComponent() {
    }
    AppComponent = __decorate([
        Object(_angular_core__WEBPACK_IMPORTED_MODULE_0__["Component"])({
            template: '<navigation-bar></navigation-bar><router-outlet></router-outlet>'
        })
    ], AppComponent);
    return AppComponent;
}());



/***/ }),

/***/ "./src/app/components/log/log.component.html":
/*!***************************************************!*\
  !*** ./src/app/components/log/log.component.html ***!
  \***************************************************/
/*! no static exports found */
/***/ (function(module, exports) {

module.exports = "<div style=\"margin-top: 54px;\">\nlog\n</div>"

/***/ }),

/***/ "./src/app/components/log/log.component.ts":
/*!*************************************************!*\
  !*** ./src/app/components/log/log.component.ts ***!
  \*************************************************/
/*! exports provided: LogComponent */
/***/ (function(module, __webpack_exports__, __webpack_require__) {

"use strict";
__webpack_require__.r(__webpack_exports__);
/* harmony export (binding) */ __webpack_require__.d(__webpack_exports__, "LogComponent", function() { return LogComponent; });
/* harmony import */ var _angular_core__WEBPACK_IMPORTED_MODULE_0__ = __webpack_require__(/*! @angular/core */ "./node_modules/@angular/core/fesm5/core.js");
/* harmony import */ var _services_auth_service__WEBPACK_IMPORTED_MODULE_1__ = __webpack_require__(/*! ../../services/auth.service */ "./src/app/services/auth.service.ts");
var __decorate = (undefined && undefined.__decorate) || function (decorators, target, key, desc) {
    var c = arguments.length, r = c < 3 ? target : desc === null ? desc = Object.getOwnPropertyDescriptor(target, key) : desc, d;
    if (typeof Reflect === "object" && typeof Reflect.decorate === "function") r = Reflect.decorate(decorators, target, key, desc);
    else for (var i = decorators.length - 1; i >= 0; i--) if (d = decorators[i]) r = (c < 3 ? d(r) : c > 3 ? d(target, key, r) : d(target, key)) || r;
    return c > 3 && r && Object.defineProperty(target, key, r), r;
};
var __metadata = (undefined && undefined.__metadata) || function (k, v) {
    if (typeof Reflect === "object" && typeof Reflect.metadata === "function") return Reflect.metadata(k, v);
};


var LogComponent = /** @class */ (function () {
    function LogComponent(authService) {
        this.authService = authService;
    }
    LogComponent = __decorate([
        Object(_angular_core__WEBPACK_IMPORTED_MODULE_0__["Component"])({
            template: __webpack_require__(/*! ./log.component.html */ "./src/app/components/log/log.component.html"),
        }),
        __metadata("design:paramtypes", [_services_auth_service__WEBPACK_IMPORTED_MODULE_1__["AuthService"]])
    ], LogComponent);
    return LogComponent;
}());



/***/ }),

/***/ "./src/app/components/login/login.component.css":
/*!******************************************************!*\
  !*** ./src/app/components/login/login.component.css ***!
  \******************************************************/
/*! no static exports found */
/***/ (function(module, exports) {

module.exports = ".background {\n    height: 100vh;\n    display: flex;\n    flex-direction: column;\n    background-color: #eeeeee;\n}\n\n.space {\n    flex: 1;\n}\n\n.content {\n    width: 25rem;\n    padding: 1rem;\n    border-radius: 0.25rem;\n    box-shadow: 0 0.05rem 0.25rem 0 rgba(0, 0, 0, 0.2);\n    background-color: white;\n\n    display: flex;\n    flex-direction: column;\n}\n\n@media only screen and (max-width: 500px) {\n    .background {\n        background-color: white;\n    }\n\n    .content {\n        width: 100%;\n        border-radius: 0;\n        box-shadow: none;\n    }\n}\n\n.heading {\n    display: flex;\n    align-items: center;\n}\n\n.title {\n    font-size: 2.5rem;\n    font-weight: 600;\n}\n\nform > .form-group {\n    margin: 1rem 0;\n}\n\nform > .form-group > label {\n    font-size: 1rem;\n    font-weight: 500;\n    margin-bottom: 0.25rem;\n    display: inline-block;\n}\n\nform > .form-group-horizontal {\n    display: flex;\n    flex-direction: row-reverse;\n    justify-content: space-between;\n    align-items: center;\n}\n\nform > .form-group-horizontal > label {\n    font-size: 1rem;\n    color: #d85452;\n}\n\ninput[type=text], input[type=password] {\n    width: 100%;\n    padding: 0.5rem;\n    border: 1px solid #ccc;\n    border-radius: 0.25rem;\n    box-sizing: border-box;\n    font-size: 1rem;\n    -webkit-appearance: none;\n}\n\ninput[type=submit] {\n    background-color: #28a745;\n    color: white;\n    padding: 0.75rem 1rem;\n    border: none;\n    border-radius: 0.25rem;\n    cursor: pointer;\n    float: right;\n    font-size: 1rem;\n    -webkit-appearance: none;\n}\n\ninput[type=submit]:hover {\n    background-color: #218838;\n}\n\ninput[type=submit]:active {\n    background-color: #1e7e34;\n}\n\ninput[type=submit]:disabled {\n    opacity: .65;\n    cursor: not-allowed;\n}\n\n.ng-invalid:not(form).ng-touched:not(form)  {\n    border-left: 5px solid #d85452;\n}\n/*# sourceMappingURL=data:application/json;base64,eyJ2ZXJzaW9uIjozLCJzb3VyY2VzIjpbInNyYy9hcHAvY29tcG9uZW50cy9sb2dpbi9sb2dpbi5jb21wb25lbnQuY3NzIl0sIm5hbWVzIjpbXSwibWFwcGluZ3MiOiJBQUFBO0lBQ0ksY0FBYztJQUNkLGNBQWM7SUFDZCx1QkFBdUI7SUFDdkIsMEJBQTBCO0NBQzdCOztBQUVEO0lBQ0ksUUFBUTtDQUNYOztBQUVEO0lBQ0ksYUFBYTtJQUNiLGNBQWM7SUFDZCx1QkFBdUI7SUFDdkIsbURBQW1EO0lBQ25ELHdCQUF3Qjs7SUFFeEIsY0FBYztJQUNkLHVCQUF1QjtDQUMxQjs7QUFFRDtJQUNJO1FBQ0ksd0JBQXdCO0tBQzNCOztJQUVEO1FBQ0ksWUFBWTtRQUNaLGlCQUFpQjtRQUNqQixpQkFBaUI7S0FDcEI7Q0FDSjs7QUFFRDtJQUNJLGNBQWM7SUFDZCxvQkFBb0I7Q0FDdkI7O0FBRUQ7SUFDSSxrQkFBa0I7SUFDbEIsaUJBQWlCO0NBQ3BCOztBQUVEO0lBQ0ksZUFBZTtDQUNsQjs7QUFFRDtJQUNJLGdCQUFnQjtJQUNoQixpQkFBaUI7SUFDakIsdUJBQXVCO0lBQ3ZCLHNCQUFzQjtDQUN6Qjs7QUFFRDtJQUNJLGNBQWM7SUFDZCw0QkFBNEI7SUFDNUIsK0JBQStCO0lBQy9CLG9CQUFvQjtDQUN2Qjs7QUFFRDtJQUNJLGdCQUFnQjtJQUNoQixlQUFlO0NBQ2xCOztBQUVEO0lBQ0ksWUFBWTtJQUNaLGdCQUFnQjtJQUNoQix1QkFBdUI7SUFDdkIsdUJBQXVCO0lBQ3ZCLHVCQUF1QjtJQUN2QixnQkFBZ0I7SUFDaEIseUJBQXlCO0NBQzVCOztBQUVEO0lBQ0ksMEJBQTBCO0lBQzFCLGFBQWE7SUFDYixzQkFBc0I7SUFDdEIsYUFBYTtJQUNiLHVCQUF1QjtJQUN2QixnQkFBZ0I7SUFDaEIsYUFBYTtJQUNiLGdCQUFnQjtJQUNoQix5QkFBeUI7Q0FDNUI7O0FBRUQ7SUFDSSwwQkFBMEI7Q0FDN0I7O0FBRUQ7SUFDSSwwQkFBMEI7Q0FDN0I7O0FBRUQ7SUFDSSxhQUFhO0lBQ2Isb0JBQW9CO0NBQ3ZCOztBQUVEO0lBQ0ksK0JBQStCO0NBQ2xDIiwiZmlsZSI6InNyYy9hcHAvY29tcG9uZW50cy9sb2dpbi9sb2dpbi5jb21wb25lbnQuY3NzIiwic291cmNlc0NvbnRlbnQiOlsiLmJhY2tncm91bmQge1xuICAgIGhlaWdodDogMTAwdmg7XG4gICAgZGlzcGxheTogZmxleDtcbiAgICBmbGV4LWRpcmVjdGlvbjogY29sdW1uO1xuICAgIGJhY2tncm91bmQtY29sb3I6ICNlZWVlZWU7XG59XG5cbi5zcGFjZSB7XG4gICAgZmxleDogMTtcbn1cblxuLmNvbnRlbnQge1xuICAgIHdpZHRoOiAyNXJlbTtcbiAgICBwYWRkaW5nOiAxcmVtO1xuICAgIGJvcmRlci1yYWRpdXM6IDAuMjVyZW07XG4gICAgYm94LXNoYWRvdzogMCAwLjA1cmVtIDAuMjVyZW0gMCByZ2JhKDAsIDAsIDAsIDAuMik7XG4gICAgYmFja2dyb3VuZC1jb2xvcjogd2hpdGU7XG5cbiAgICBkaXNwbGF5OiBmbGV4O1xuICAgIGZsZXgtZGlyZWN0aW9uOiBjb2x1bW47XG59XG5cbkBtZWRpYSBvbmx5IHNjcmVlbiBhbmQgKG1heC13aWR0aDogNTAwcHgpIHtcbiAgICAuYmFja2dyb3VuZCB7XG4gICAgICAgIGJhY2tncm91bmQtY29sb3I6IHdoaXRlO1xuICAgIH1cblxuICAgIC5jb250ZW50IHtcbiAgICAgICAgd2lkdGg6IDEwMCU7XG4gICAgICAgIGJvcmRlci1yYWRpdXM6IDA7XG4gICAgICAgIGJveC1zaGFkb3c6IG5vbmU7XG4gICAgfVxufVxuXG4uaGVhZGluZyB7XG4gICAgZGlzcGxheTogZmxleDtcbiAgICBhbGlnbi1pdGVtczogY2VudGVyO1xufVxuXG4udGl0bGUge1xuICAgIGZvbnQtc2l6ZTogMi41cmVtO1xuICAgIGZvbnQtd2VpZ2h0OiA2MDA7XG59XG5cbmZvcm0gPiAuZm9ybS1ncm91cCB7XG4gICAgbWFyZ2luOiAxcmVtIDA7XG59XG5cbmZvcm0gPiAuZm9ybS1ncm91cCA+IGxhYmVsIHtcbiAgICBmb250LXNpemU6IDFyZW07XG4gICAgZm9udC13ZWlnaHQ6IDUwMDtcbiAgICBtYXJnaW4tYm90dG9tOiAwLjI1cmVtO1xuICAgIGRpc3BsYXk6IGlubGluZS1ibG9jaztcbn1cblxuZm9ybSA+IC5mb3JtLWdyb3VwLWhvcml6b250YWwge1xuICAgIGRpc3BsYXk6IGZsZXg7XG4gICAgZmxleC1kaXJlY3Rpb246IHJvdy1yZXZlcnNlO1xuICAgIGp1c3RpZnktY29udGVudDogc3BhY2UtYmV0d2VlbjtcbiAgICBhbGlnbi1pdGVtczogY2VudGVyO1xufVxuXG5mb3JtID4gLmZvcm0tZ3JvdXAtaG9yaXpvbnRhbCA+IGxhYmVsIHtcbiAgICBmb250LXNpemU6IDFyZW07XG4gICAgY29sb3I6ICNkODU0NTI7XG59XG5cbmlucHV0W3R5cGU9dGV4dF0sIGlucHV0W3R5cGU9cGFzc3dvcmRdIHtcbiAgICB3aWR0aDogMTAwJTtcbiAgICBwYWRkaW5nOiAwLjVyZW07XG4gICAgYm9yZGVyOiAxcHggc29saWQgI2NjYztcbiAgICBib3JkZXItcmFkaXVzOiAwLjI1cmVtO1xuICAgIGJveC1zaXppbmc6IGJvcmRlci1ib3g7XG4gICAgZm9udC1zaXplOiAxcmVtO1xuICAgIC13ZWJraXQtYXBwZWFyYW5jZTogbm9uZTtcbn1cblxuaW5wdXRbdHlwZT1zdWJtaXRdIHtcbiAgICBiYWNrZ3JvdW5kLWNvbG9yOiAjMjhhNzQ1O1xuICAgIGNvbG9yOiB3aGl0ZTtcbiAgICBwYWRkaW5nOiAwLjc1cmVtIDFyZW07XG4gICAgYm9yZGVyOiBub25lO1xuICAgIGJvcmRlci1yYWRpdXM6IDAuMjVyZW07XG4gICAgY3Vyc29yOiBwb2ludGVyO1xuICAgIGZsb2F0OiByaWdodDtcbiAgICBmb250LXNpemU6IDFyZW07XG4gICAgLXdlYmtpdC1hcHBlYXJhbmNlOiBub25lO1xufVxuXG5pbnB1dFt0eXBlPXN1Ym1pdF06aG92ZXIge1xuICAgIGJhY2tncm91bmQtY29sb3I6ICMyMTg4Mzg7XG59XG5cbmlucHV0W3R5cGU9c3VibWl0XTphY3RpdmUge1xuICAgIGJhY2tncm91bmQtY29sb3I6ICMxZTdlMzQ7XG59XG5cbmlucHV0W3R5cGU9c3VibWl0XTpkaXNhYmxlZCB7XG4gICAgb3BhY2l0eTogLjY1O1xuICAgIGN1cnNvcjogbm90LWFsbG93ZWQ7XG59XG5cbi5uZy1pbnZhbGlkOm5vdChmb3JtKS5uZy10b3VjaGVkOm5vdChmb3JtKSAge1xuICAgIGJvcmRlci1sZWZ0OiA1cHggc29saWQgI2Q4NTQ1Mjtcbn0iXX0= */"

/***/ }),

/***/ "./src/app/components/login/login.component.html":
/*!*******************************************************!*\
  !*** ./src/app/components/login/login.component.html ***!
  \*******************************************************/
/*! no static exports found */
/***/ (function(module, exports) {

module.exports = "<div class=\"background\">\n    <div class=\"space\"></div>\n    <div style=\"display: flex;\">\n        <div class=\"space\"></div>\n        <div class=\"content\">\n            <div class=\"heading\">\n                <img src=\"assets/favicon.svg\" width=\"35rem\" style=\"margin-right: 1rem;\">\n                <span class=\"title\">Zimfarm</span>\n            </div>\n            <form #loginForm=\"ngForm\" (ngSubmit)=\"login()\">\n                <div class=\"form-group\">\n                    <label for=\"username\">Username:</label>\n                    <input type=\"text\" id=\"username\" name=\"username\" [(ngModel)]=\"username\" (ngModelChange)=\"valueChanged()\" required> \n                </div>\n                <div class=\"form-group\">\n                    <label for=\"password\">Password:</label>\n                    <input type=\"password\" id=\"password\" name=\"password\" [(ngModel)]=\"password\" (ngModelChange)=\"valueChanged()\" required>\n                </div>\n                <div class=\"form-group-horizontal\">\n                    <input [disabled]=\"loginForm.invalid\" type=\"submit\" value=\"Login\">\n                    <label [hidden]=\"loginForm.valid || loginForm.untouched\">\n                        Please enter valid username and password.\n                    </label>\n                    <label [hidden]=\"hideInvalidCredential\">\n                        Username or password not correct.\n                    </label>\n                </div>\n            </form>\n        </div>\n        <div class=\"space\"></div>\n    </div>\n    <div class=\"space\"></div>\n    <div class=\"space\"></div>\n</div>\n"

/***/ }),

/***/ "./src/app/components/login/login.component.ts":
/*!*****************************************************!*\
  !*** ./src/app/components/login/login.component.ts ***!
  \*****************************************************/
/*! exports provided: LoginComponent */
/***/ (function(module, __webpack_exports__, __webpack_require__) {

"use strict";
__webpack_require__.r(__webpack_exports__);
/* harmony export (binding) */ __webpack_require__.d(__webpack_exports__, "LoginComponent", function() { return LoginComponent; });
/* harmony import */ var _angular_core__WEBPACK_IMPORTED_MODULE_0__ = __webpack_require__(/*! @angular/core */ "./node_modules/@angular/core/fesm5/core.js");
/* harmony import */ var _angular_router__WEBPACK_IMPORTED_MODULE_1__ = __webpack_require__(/*! @angular/router */ "./node_modules/@angular/router/fesm5/router.js");
/* harmony import */ var _services_auth_service__WEBPACK_IMPORTED_MODULE_2__ = __webpack_require__(/*! ../../services/auth.service */ "./src/app/services/auth.service.ts");
var __decorate = (undefined && undefined.__decorate) || function (decorators, target, key, desc) {
    var c = arguments.length, r = c < 3 ? target : desc === null ? desc = Object.getOwnPropertyDescriptor(target, key) : desc, d;
    if (typeof Reflect === "object" && typeof Reflect.decorate === "function") r = Reflect.decorate(decorators, target, key, desc);
    else for (var i = decorators.length - 1; i >= 0; i--) if (d = decorators[i]) r = (c < 3 ? d(r) : c > 3 ? d(target, key, r) : d(target, key)) || r;
    return c > 3 && r && Object.defineProperty(target, key, r), r;
};
var __metadata = (undefined && undefined.__metadata) || function (k, v) {
    if (typeof Reflect === "object" && typeof Reflect.metadata === "function") return Reflect.metadata(k, v);
};



var LoginComponent = /** @class */ (function () {
    function LoginComponent(router, authService) {
        this.router = router;
        this.authService = authService;
        this.hideInvalidCredential = true;
    }
    LoginComponent.prototype.ngOnInit = function () {
        this.authService.logOut();
    };
    LoginComponent.prototype.login = function () {
        var _this = this;
        this.authService.authorize(this.username, this.password).subscribe(function (data) {
            _this.hideInvalidCredential = true;
            _this.router.navigate(['']);
        }, function (error) {
            _this.hideInvalidCredential = false;
        });
    };
    LoginComponent.prototype.valueChanged = function () {
        this.hideInvalidCredential = true;
    };
    LoginComponent = __decorate([
        Object(_angular_core__WEBPACK_IMPORTED_MODULE_0__["Component"])({
            template: __webpack_require__(/*! ./login.component.html */ "./src/app/components/login/login.component.html"),
            styles: [__webpack_require__(/*! ./login.component.css */ "./src/app/components/login/login.component.css")]
        }),
        __metadata("design:paramtypes", [_angular_router__WEBPACK_IMPORTED_MODULE_1__["Router"], _services_auth_service__WEBPACK_IMPORTED_MODULE_2__["AuthService"]])
    ], LoginComponent);
    return LoginComponent;
}());



/***/ }),

/***/ "./src/app/components/navigation-bar/navigation-bar.component.css":
/*!************************************************************************!*\
  !*** ./src/app/components/navigation-bar/navigation-bar.component.css ***!
  \************************************************************************/
/*! no static exports found */
/***/ (function(module, exports) {

module.exports = ".navbar {\n    overflow: hidden;\n    background-color: #eeeeee;\n    position: fixed;\n    top: 0;\n    height: 54px;\n    width: 100%;\n    box-shadow: 0 0.05rem 0.25rem 0 rgba(0, 0, 0, 0.3);\n    box-sizing: border-box;\n    overflow-x: auto;\n    display: flex;\n    align-items: stretch;\n    padding-left: env(safe-area-inset-left);\n    padding-right: env(safe-area-inset-right);\n}\n\n.navbar > .logo {\n    margin-left: 1rem;\n    margin-right: 0.5rem;\n    display: flex;\n    align-items: center;\n}\n\n@media (max-width: 560px) {\n    .navbar > .logo {\n        display: none;\n    }\n}\n\n.navbar label {\n    font-size: 1.5rem;\n    font-weight: 500;\n}\n\n.navbar .item {\n    margin: 0 0.5rem;\n    display: flex;\n    align-items: stretch;\n}\n\n.navbar a {\n    color: gray;\n    text-decoration: none;\n    font-size: 1rem;\n    font-weight: 400;\n    display: flex;\n    align-items: center;\n    padding: 0 1rem;\n}\n\n.navbar a:hover {\n    background: #ddd;\n    color: black;\n}\n\n.navbar a.active {\n    background: #ddd;\n    color: black;\n}\n/*# sourceMappingURL=data:application/json;base64,eyJ2ZXJzaW9uIjozLCJzb3VyY2VzIjpbInNyYy9hcHAvY29tcG9uZW50cy9uYXZpZ2F0aW9uLWJhci9uYXZpZ2F0aW9uLWJhci5jb21wb25lbnQuY3NzIl0sIm5hbWVzIjpbXSwibWFwcGluZ3MiOiJBQUFBO0lBQ0ksaUJBQWlCO0lBQ2pCLDBCQUEwQjtJQUMxQixnQkFBZ0I7SUFDaEIsT0FBTztJQUNQLGFBQWE7SUFDYixZQUFZO0lBQ1osbURBQW1EO0lBQ25ELHVCQUF1QjtJQUN2QixpQkFBaUI7SUFDakIsY0FBYztJQUNkLHFCQUFxQjtJQUNyQix3Q0FBd0M7SUFDeEMsMENBQTBDO0NBQzdDOztBQUVEO0lBQ0ksa0JBQWtCO0lBQ2xCLHFCQUFxQjtJQUNyQixjQUFjO0lBQ2Qsb0JBQW9CO0NBQ3ZCOztBQUVEO0lBQ0k7UUFDSSxjQUFjO0tBQ2pCO0NBQ0o7O0FBRUQ7SUFDSSxrQkFBa0I7SUFDbEIsaUJBQWlCO0NBQ3BCOztBQUVEO0lBQ0ksaUJBQWlCO0lBQ2pCLGNBQWM7SUFDZCxxQkFBcUI7Q0FDeEI7O0FBRUQ7SUFDSSxZQUFZO0lBQ1osc0JBQXNCO0lBQ3RCLGdCQUFnQjtJQUNoQixpQkFBaUI7SUFDakIsY0FBYztJQUNkLG9CQUFvQjtJQUNwQixnQkFBZ0I7Q0FDbkI7O0FBRUQ7SUFDSSxpQkFBaUI7SUFDakIsYUFBYTtDQUNoQjs7QUFFRDtJQUNJLGlCQUFpQjtJQUNqQixhQUFhO0NBQ2hCIiwiZmlsZSI6InNyYy9hcHAvY29tcG9uZW50cy9uYXZpZ2F0aW9uLWJhci9uYXZpZ2F0aW9uLWJhci5jb21wb25lbnQuY3NzIiwic291cmNlc0NvbnRlbnQiOlsiLm5hdmJhciB7XG4gICAgb3ZlcmZsb3c6IGhpZGRlbjtcbiAgICBiYWNrZ3JvdW5kLWNvbG9yOiAjZWVlZWVlO1xuICAgIHBvc2l0aW9uOiBmaXhlZDtcbiAgICB0b3A6IDA7XG4gICAgaGVpZ2h0OiA1NHB4O1xuICAgIHdpZHRoOiAxMDAlO1xuICAgIGJveC1zaGFkb3c6IDAgMC4wNXJlbSAwLjI1cmVtIDAgcmdiYSgwLCAwLCAwLCAwLjMpO1xuICAgIGJveC1zaXppbmc6IGJvcmRlci1ib3g7XG4gICAgb3ZlcmZsb3cteDogYXV0bztcbiAgICBkaXNwbGF5OiBmbGV4O1xuICAgIGFsaWduLWl0ZW1zOiBzdHJldGNoO1xuICAgIHBhZGRpbmctbGVmdDogZW52KHNhZmUtYXJlYS1pbnNldC1sZWZ0KTtcbiAgICBwYWRkaW5nLXJpZ2h0OiBlbnYoc2FmZS1hcmVhLWluc2V0LXJpZ2h0KTtcbn1cblxuLm5hdmJhciA+IC5sb2dvIHtcbiAgICBtYXJnaW4tbGVmdDogMXJlbTtcbiAgICBtYXJnaW4tcmlnaHQ6IDAuNXJlbTtcbiAgICBkaXNwbGF5OiBmbGV4O1xuICAgIGFsaWduLWl0ZW1zOiBjZW50ZXI7XG59XG5cbkBtZWRpYSAobWF4LXdpZHRoOiA1NjBweCkge1xuICAgIC5uYXZiYXIgPiAubG9nbyB7XG4gICAgICAgIGRpc3BsYXk6IG5vbmU7XG4gICAgfVxufVxuXG4ubmF2YmFyIGxhYmVsIHtcbiAgICBmb250LXNpemU6IDEuNXJlbTtcbiAgICBmb250LXdlaWdodDogNTAwO1xufVxuXG4ubmF2YmFyIC5pdGVtIHtcbiAgICBtYXJnaW46IDAgMC41cmVtO1xuICAgIGRpc3BsYXk6IGZsZXg7XG4gICAgYWxpZ24taXRlbXM6IHN0cmV0Y2g7XG59XG5cbi5uYXZiYXIgYSB7XG4gICAgY29sb3I6IGdyYXk7XG4gICAgdGV4dC1kZWNvcmF0aW9uOiBub25lO1xuICAgIGZvbnQtc2l6ZTogMXJlbTtcbiAgICBmb250LXdlaWdodDogNDAwO1xuICAgIGRpc3BsYXk6IGZsZXg7XG4gICAgYWxpZ24taXRlbXM6IGNlbnRlcjtcbiAgICBwYWRkaW5nOiAwIDFyZW07XG59XG5cbi5uYXZiYXIgYTpob3ZlciB7XG4gICAgYmFja2dyb3VuZDogI2RkZDtcbiAgICBjb2xvcjogYmxhY2s7XG59XG5cbi5uYXZiYXIgYS5hY3RpdmUge1xuICAgIGJhY2tncm91bmQ6ICNkZGQ7XG4gICAgY29sb3I6IGJsYWNrO1xufSJdfQ== */"

/***/ }),

/***/ "./src/app/components/navigation-bar/navigation-bar.component.html":
/*!*************************************************************************!*\
  !*** ./src/app/components/navigation-bar/navigation-bar.component.html ***!
  \*************************************************************************/
/*! no static exports found */
/***/ (function(module, exports) {

module.exports = "<div class=\"navbar\">\n    <div class=\"logo\">\n        <img src=\"assets/favicon.svg\" width=\"30rem\" style=\"margin-right: 0.5rem;\">\n        <label>Zimfarm</label>\n    </div>\n    <div class=\"item\">\n        <a routerLink=\"/schedule\" routerLinkActive=\"active\">Schedule</a>\n        <a routerLink=\"/queue\" routerLinkActive=\"active\">Queue</a>\n        <a routerLink=\"/worker\" routerLinkActive=\"active\">Worker</a>\n        <a routerLink=\"/log\" routerLinkActive=\"active\">Log</a>\n    </div>\n    <div style=\"flex: 1;\"></div>\n    <div class=\"item\">\n        <a routerLink=\"/user\" routerLinkActive=\"active\">User</a>\n    </div>\n</div>"

/***/ }),

/***/ "./src/app/components/navigation-bar/navigation-bar.component.ts":
/*!***********************************************************************!*\
  !*** ./src/app/components/navigation-bar/navigation-bar.component.ts ***!
  \***********************************************************************/
/*! exports provided: NavigationBarComponent */
/***/ (function(module, __webpack_exports__, __webpack_require__) {

"use strict";
__webpack_require__.r(__webpack_exports__);
/* harmony export (binding) */ __webpack_require__.d(__webpack_exports__, "NavigationBarComponent", function() { return NavigationBarComponent; });
/* harmony import */ var _angular_core__WEBPACK_IMPORTED_MODULE_0__ = __webpack_require__(/*! @angular/core */ "./node_modules/@angular/core/fesm5/core.js");
var __decorate = (undefined && undefined.__decorate) || function (decorators, target, key, desc) {
    var c = arguments.length, r = c < 3 ? target : desc === null ? desc = Object.getOwnPropertyDescriptor(target, key) : desc, d;
    if (typeof Reflect === "object" && typeof Reflect.decorate === "function") r = Reflect.decorate(decorators, target, key, desc);
    else for (var i = decorators.length - 1; i >= 0; i--) if (d = decorators[i]) r = (c < 3 ? d(r) : c > 3 ? d(target, key, r) : d(target, key)) || r;
    return c > 3 && r && Object.defineProperty(target, key, r), r;
};

var NavigationBarComponent = /** @class */ (function () {
    function NavigationBarComponent() {
    }
    NavigationBarComponent = __decorate([
        Object(_angular_core__WEBPACK_IMPORTED_MODULE_0__["Component"])({
            selector: 'navigation-bar',
            template: __webpack_require__(/*! ./navigation-bar.component.html */ "./src/app/components/navigation-bar/navigation-bar.component.html"),
            styles: [__webpack_require__(/*! ./navigation-bar.component.css */ "./src/app/components/navigation-bar/navigation-bar.component.css")]
        })
    ], NavigationBarComponent);
    return NavigationBarComponent;
}());



/***/ }),

/***/ "./src/app/components/queue/queue.component.html":
/*!*******************************************************!*\
  !*** ./src/app/components/queue/queue.component.html ***!
  \*******************************************************/
/*! no static exports found */
/***/ (function(module, exports) {

module.exports = "<div style=\"margin-top: 54px;\">\n        queue\n        queue\n        queue\n        queue\n        queue\n        queue\n        \n</div>"

/***/ }),

/***/ "./src/app/components/queue/queue.component.ts":
/*!*****************************************************!*\
  !*** ./src/app/components/queue/queue.component.ts ***!
  \*****************************************************/
/*! exports provided: QueueComponent */
/***/ (function(module, __webpack_exports__, __webpack_require__) {

"use strict";
__webpack_require__.r(__webpack_exports__);
/* harmony export (binding) */ __webpack_require__.d(__webpack_exports__, "QueueComponent", function() { return QueueComponent; });
/* harmony import */ var _angular_core__WEBPACK_IMPORTED_MODULE_0__ = __webpack_require__(/*! @angular/core */ "./node_modules/@angular/core/fesm5/core.js");
/* harmony import */ var _services_auth_service__WEBPACK_IMPORTED_MODULE_1__ = __webpack_require__(/*! ../../services/auth.service */ "./src/app/services/auth.service.ts");
var __decorate = (undefined && undefined.__decorate) || function (decorators, target, key, desc) {
    var c = arguments.length, r = c < 3 ? target : desc === null ? desc = Object.getOwnPropertyDescriptor(target, key) : desc, d;
    if (typeof Reflect === "object" && typeof Reflect.decorate === "function") r = Reflect.decorate(decorators, target, key, desc);
    else for (var i = decorators.length - 1; i >= 0; i--) if (d = decorators[i]) r = (c < 3 ? d(r) : c > 3 ? d(target, key, r) : d(target, key)) || r;
    return c > 3 && r && Object.defineProperty(target, key, r), r;
};
var __metadata = (undefined && undefined.__metadata) || function (k, v) {
    if (typeof Reflect === "object" && typeof Reflect.metadata === "function") return Reflect.metadata(k, v);
};


var QueueComponent = /** @class */ (function () {
    function QueueComponent(authService) {
        this.authService = authService;
    }
    QueueComponent = __decorate([
        Object(_angular_core__WEBPACK_IMPORTED_MODULE_0__["Component"])({
            template: __webpack_require__(/*! ./queue.component.html */ "./src/app/components/queue/queue.component.html"),
        }),
        __metadata("design:paramtypes", [_services_auth_service__WEBPACK_IMPORTED_MODULE_1__["AuthService"]])
    ], QueueComponent);
    return QueueComponent;
}());



/***/ }),

/***/ "./src/app/components/user/user.component.css":
/*!****************************************************!*\
  !*** ./src/app/components/user/user.component.css ***!
  \****************************************************/
/*! no static exports found */
/***/ (function(module, exports) {

module.exports = ".content {\n    margin-top: 54px;\n    padding: 1rem;\n    display: flex;\n    flex-direction: column;\n    align-items: center;\n    \n}\n\n\n/*# sourceMappingURL=data:application/json;base64,eyJ2ZXJzaW9uIjozLCJzb3VyY2VzIjpbInNyYy9hcHAvY29tcG9uZW50cy91c2VyL3VzZXIuY29tcG9uZW50LmNzcyJdLCJuYW1lcyI6W10sIm1hcHBpbmdzIjoiQUFBQTtJQUNJLGlCQUFpQjtJQUNqQixjQUFjO0lBQ2QsY0FBYztJQUNkLHVCQUF1QjtJQUN2QixvQkFBb0I7O0NBRXZCIiwiZmlsZSI6InNyYy9hcHAvY29tcG9uZW50cy91c2VyL3VzZXIuY29tcG9uZW50LmNzcyIsInNvdXJjZXNDb250ZW50IjpbIi5jb250ZW50IHtcbiAgICBtYXJnaW4tdG9wOiA1NHB4O1xuICAgIHBhZGRpbmc6IDFyZW07XG4gICAgZGlzcGxheTogZmxleDtcbiAgICBmbGV4LWRpcmVjdGlvbjogY29sdW1uO1xuICAgIGFsaWduLWl0ZW1zOiBjZW50ZXI7XG4gICAgXG59XG5cbiJdfQ== */"

/***/ }),

/***/ "./src/app/components/user/user.component.html":
/*!*****************************************************!*\
  !*** ./src/app/components/user/user.component.html ***!
  \*****************************************************/
/*! no static exports found */
/***/ (function(module, exports) {

module.exports = "<div class=\"content\">\n    <button class=\"success\" (click)=\"logOut()\">Log out</button>\n</div>"

/***/ }),

/***/ "./src/app/components/user/user.component.ts":
/*!***************************************************!*\
  !*** ./src/app/components/user/user.component.ts ***!
  \***************************************************/
/*! exports provided: UserComponent */
/***/ (function(module, __webpack_exports__, __webpack_require__) {

"use strict";
__webpack_require__.r(__webpack_exports__);
/* harmony export (binding) */ __webpack_require__.d(__webpack_exports__, "UserComponent", function() { return UserComponent; });
/* harmony import */ var _angular_core__WEBPACK_IMPORTED_MODULE_0__ = __webpack_require__(/*! @angular/core */ "./node_modules/@angular/core/fesm5/core.js");
/* harmony import */ var _angular_router__WEBPACK_IMPORTED_MODULE_1__ = __webpack_require__(/*! @angular/router */ "./node_modules/@angular/router/fesm5/router.js");
/* harmony import */ var _services_auth_service__WEBPACK_IMPORTED_MODULE_2__ = __webpack_require__(/*! ../../services/auth.service */ "./src/app/services/auth.service.ts");
var __decorate = (undefined && undefined.__decorate) || function (decorators, target, key, desc) {
    var c = arguments.length, r = c < 3 ? target : desc === null ? desc = Object.getOwnPropertyDescriptor(target, key) : desc, d;
    if (typeof Reflect === "object" && typeof Reflect.decorate === "function") r = Reflect.decorate(decorators, target, key, desc);
    else for (var i = decorators.length - 1; i >= 0; i--) if (d = decorators[i]) r = (c < 3 ? d(r) : c > 3 ? d(target, key, r) : d(target, key)) || r;
    return c > 3 && r && Object.defineProperty(target, key, r), r;
};
var __metadata = (undefined && undefined.__metadata) || function (k, v) {
    if (typeof Reflect === "object" && typeof Reflect.metadata === "function") return Reflect.metadata(k, v);
};



var UserComponent = /** @class */ (function () {
    function UserComponent(router, authService) {
        this.router = router;
        this.authService = authService;
    }
    UserComponent.prototype.logOut = function () {
        this.authService.logOut();
        this.router.navigate(['login']);
    };
    UserComponent = __decorate([
        Object(_angular_core__WEBPACK_IMPORTED_MODULE_0__["Component"])({
            template: __webpack_require__(/*! ./user.component.html */ "./src/app/components/user/user.component.html"),
            styles: [__webpack_require__(/*! ./user.component.css */ "./src/app/components/user/user.component.css")]
        }),
        __metadata("design:paramtypes", [_angular_router__WEBPACK_IMPORTED_MODULE_1__["Router"], _services_auth_service__WEBPACK_IMPORTED_MODULE_2__["AuthService"]])
    ], UserComponent);
    return UserComponent;
}());



/***/ }),

/***/ "./src/app/components/worker/worker.component.html":
/*!*********************************************************!*\
  !*** ./src/app/components/worker/worker.component.html ***!
  \*********************************************************/
/*! no static exports found */
/***/ (function(module, exports) {

module.exports = "<div style=\"margin-top: 54px;\">\nworker\n</div>"

/***/ }),

/***/ "./src/app/components/worker/worker.component.ts":
/*!*******************************************************!*\
  !*** ./src/app/components/worker/worker.component.ts ***!
  \*******************************************************/
/*! exports provided: WorkerComponent */
/***/ (function(module, __webpack_exports__, __webpack_require__) {

"use strict";
__webpack_require__.r(__webpack_exports__);
/* harmony export (binding) */ __webpack_require__.d(__webpack_exports__, "WorkerComponent", function() { return WorkerComponent; });
/* harmony import */ var _angular_core__WEBPACK_IMPORTED_MODULE_0__ = __webpack_require__(/*! @angular/core */ "./node_modules/@angular/core/fesm5/core.js");
/* harmony import */ var _services_auth_service__WEBPACK_IMPORTED_MODULE_1__ = __webpack_require__(/*! ../../services/auth.service */ "./src/app/services/auth.service.ts");
var __decorate = (undefined && undefined.__decorate) || function (decorators, target, key, desc) {
    var c = arguments.length, r = c < 3 ? target : desc === null ? desc = Object.getOwnPropertyDescriptor(target, key) : desc, d;
    if (typeof Reflect === "object" && typeof Reflect.decorate === "function") r = Reflect.decorate(decorators, target, key, desc);
    else for (var i = decorators.length - 1; i >= 0; i--) if (d = decorators[i]) r = (c < 3 ? d(r) : c > 3 ? d(target, key, r) : d(target, key)) || r;
    return c > 3 && r && Object.defineProperty(target, key, r), r;
};
var __metadata = (undefined && undefined.__metadata) || function (k, v) {
    if (typeof Reflect === "object" && typeof Reflect.metadata === "function") return Reflect.metadata(k, v);
};


var WorkerComponent = /** @class */ (function () {
    function WorkerComponent(authService) {
        this.authService = authService;
    }
    WorkerComponent = __decorate([
        Object(_angular_core__WEBPACK_IMPORTED_MODULE_0__["Component"])({
            template: __webpack_require__(/*! ./worker.component.html */ "./src/app/components/worker/worker.component.html"),
        }),
        __metadata("design:paramtypes", [_services_auth_service__WEBPACK_IMPORTED_MODULE_1__["AuthService"]])
    ], WorkerComponent);
    return WorkerComponent;
}());



/***/ }),

/***/ "./src/app/guards/auth.guard.ts":
/*!**************************************!*\
  !*** ./src/app/guards/auth.guard.ts ***!
  \**************************************/
/*! exports provided: AuthGuard */
/***/ (function(module, __webpack_exports__, __webpack_require__) {

"use strict";
__webpack_require__.r(__webpack_exports__);
/* harmony export (binding) */ __webpack_require__.d(__webpack_exports__, "AuthGuard", function() { return AuthGuard; });
/* harmony import */ var _angular_core__WEBPACK_IMPORTED_MODULE_0__ = __webpack_require__(/*! @angular/core */ "./node_modules/@angular/core/fesm5/core.js");
/* harmony import */ var _angular_router__WEBPACK_IMPORTED_MODULE_1__ = __webpack_require__(/*! @angular/router */ "./node_modules/@angular/router/fesm5/router.js");
/* harmony import */ var _services_auth_service__WEBPACK_IMPORTED_MODULE_2__ = __webpack_require__(/*! ../services/auth.service */ "./src/app/services/auth.service.ts");
var __decorate = (undefined && undefined.__decorate) || function (decorators, target, key, desc) {
    var c = arguments.length, r = c < 3 ? target : desc === null ? desc = Object.getOwnPropertyDescriptor(target, key) : desc, d;
    if (typeof Reflect === "object" && typeof Reflect.decorate === "function") r = Reflect.decorate(decorators, target, key, desc);
    else for (var i = decorators.length - 1; i >= 0; i--) if (d = decorators[i]) r = (c < 3 ? d(r) : c > 3 ? d(target, key, r) : d(target, key)) || r;
    return c > 3 && r && Object.defineProperty(target, key, r), r;
};
var __metadata = (undefined && undefined.__metadata) || function (k, v) {
    if (typeof Reflect === "object" && typeof Reflect.metadata === "function") return Reflect.metadata(k, v);
};



var AuthGuard = /** @class */ (function () {
    function AuthGuard(authService, router) {
        this.authService = authService;
        this.router = router;
    }
    AuthGuard.prototype.canActivate = function (route, state) {
        if (this.authService.refreshToken == null) {
            this.router.navigate(['login']);
            return false;
        }
        var refreshTokenExpire = this.authService.refreshTokenExpire;
        if (refreshTokenExpire != null && refreshTokenExpire > new Date()) {
            return true;
        }
        else {
            this.router.navigate(['login']);
            return false;
        }
    };
    AuthGuard = __decorate([
        Object(_angular_core__WEBPACK_IMPORTED_MODULE_0__["Injectable"])(),
        __metadata("design:paramtypes", [_services_auth_service__WEBPACK_IMPORTED_MODULE_2__["AuthService"], _angular_router__WEBPACK_IMPORTED_MODULE_1__["Router"]])
    ], AuthGuard);
    return AuthGuard;
}());



/***/ }),

/***/ "./src/app/services/auth.service.ts":
/*!******************************************!*\
  !*** ./src/app/services/auth.service.ts ***!
  \******************************************/
/*! exports provided: AuthService, AccessTokenInterceptor */
/***/ (function(module, __webpack_exports__, __webpack_require__) {

"use strict";
__webpack_require__.r(__webpack_exports__);
/* harmony export (binding) */ __webpack_require__.d(__webpack_exports__, "AuthService", function() { return AuthService; });
/* harmony export (binding) */ __webpack_require__.d(__webpack_exports__, "AccessTokenInterceptor", function() { return AccessTokenInterceptor; });
/* harmony import */ var rxjs__WEBPACK_IMPORTED_MODULE_0__ = __webpack_require__(/*! rxjs */ "./node_modules/rxjs/_esm5/index.js");
/* harmony import */ var _angular_core__WEBPACK_IMPORTED_MODULE_1__ = __webpack_require__(/*! @angular/core */ "./node_modules/@angular/core/fesm5/core.js");
/* harmony import */ var _angular_router__WEBPACK_IMPORTED_MODULE_2__ = __webpack_require__(/*! @angular/router */ "./node_modules/@angular/router/fesm5/router.js");
/* harmony import */ var _angular_common_http__WEBPACK_IMPORTED_MODULE_3__ = __webpack_require__(/*! @angular/common/http */ "./node_modules/@angular/common/fesm5/http.js");
/* harmony import */ var rxjs_operators__WEBPACK_IMPORTED_MODULE_4__ = __webpack_require__(/*! rxjs/operators */ "./node_modules/rxjs/_esm5/operators/index.js");
/* harmony import */ var _config__WEBPACK_IMPORTED_MODULE_5__ = __webpack_require__(/*! ./config */ "./src/app/services/config.ts");
var __decorate = (undefined && undefined.__decorate) || function (decorators, target, key, desc) {
    var c = arguments.length, r = c < 3 ? target : desc === null ? desc = Object.getOwnPropertyDescriptor(target, key) : desc, d;
    if (typeof Reflect === "object" && typeof Reflect.decorate === "function") r = Reflect.decorate(decorators, target, key, desc);
    else for (var i = decorators.length - 1; i >= 0; i--) if (d = decorators[i]) r = (c < 3 ? d(r) : c > 3 ? d(target, key, r) : d(target, key)) || r;
    return c > 3 && r && Object.defineProperty(target, key, r), r;
};
var __metadata = (undefined && undefined.__metadata) || function (k, v) {
    if (typeof Reflect === "object" && typeof Reflect.metadata === "function") return Reflect.metadata(k, v);
};






var AuthService = /** @class */ (function () {
    function AuthService(http) {
        this.http = http;
    }
    AuthService.prototype.authorize = function (username, password) {
        var _this = this;
        var header = new _angular_common_http__WEBPACK_IMPORTED_MODULE_3__["HttpHeaders"]({
            'username': username,
            'password': password
        });
        return this.http.post(_config__WEBPACK_IMPORTED_MODULE_5__["apiRoot"] + '/api/auth/authorize', null, { headers: header }).pipe(Object(rxjs_operators__WEBPACK_IMPORTED_MODULE_4__["map"])(function (data) {
            _this.accessToken = data.access_token;
            _this.refreshToken = data.refresh_token;
            _this.refreshTokenExpire = new Date(Date.now() + 30 * 24 * 3600000);
            return data;
        }));
    };
    AuthService.prototype.refresh = function (refreshToken) {
        var _this = this;
        var header = new _angular_common_http__WEBPACK_IMPORTED_MODULE_3__["HttpHeaders"]({ 'refresh-token': refreshToken });
        return this.http.post(_config__WEBPACK_IMPORTED_MODULE_5__["apiRoot"] + '/api/auth/token', null, { headers: header }).pipe(Object(rxjs_operators__WEBPACK_IMPORTED_MODULE_4__["map"])(function (data) {
            _this.accessToken = data.access_token;
            _this.refreshToken = data.refresh_token;
            _this.refreshTokenExpire = new Date(Date.now() + 30 * 24 * 3600000);
            return data;
        }), Object(rxjs_operators__WEBPACK_IMPORTED_MODULE_4__["catchError"])(function (error, caught) {
            // redirect back to login
            return Object(rxjs__WEBPACK_IMPORTED_MODULE_0__["throwError"])(error);
        }));
    };
    AuthService.prototype.logOut = function () {
        localStorage.removeItem('zimfarm.access_token');
        localStorage.removeItem('zimfarm.refresh_token');
        localStorage.removeItem('zimfarm.refresh_token_expire');
    };
    Object.defineProperty(AuthService.prototype, "accessToken", {
        get: function () { return localStorage.getItem('zimfarm.access_token'); },
        set: function (token) { localStorage.setItem('zimfarm.access_token', token); },
        enumerable: true,
        configurable: true
    });
    Object.defineProperty(AuthService.prototype, "refreshToken", {
        get: function () { return localStorage.getItem('zimfarm.refresh_token'); },
        set: function (token) { localStorage.setItem('zimfarm.refresh_token', token); },
        enumerable: true,
        configurable: true
    });
    Object.defineProperty(AuthService.prototype, "refreshTokenExpire", {
        get: function () {
            var data = localStorage.getItem('zimfarm.refresh_token_expire');
            return data == null ? null : new Date(data);
        },
        set: function (date) { localStorage.setItem('zimfarm.refresh_token_expire', date.toString()); },
        enumerable: true,
        configurable: true
    });
    AuthService = __decorate([
        Object(_angular_core__WEBPACK_IMPORTED_MODULE_1__["Injectable"])({
            providedIn: 'root',
        }),
        __metadata("design:paramtypes", [_angular_common_http__WEBPACK_IMPORTED_MODULE_3__["HttpClient"]])
    ], AuthService);
    return AuthService;
}());

var AccessTokenInterceptor = /** @class */ (function () {
    function AccessTokenInterceptor(authService, router) {
        this.authService = authService;
        this.router = router;
    }
    // https://medium.com/@alexandrubereghici/angular-tutorial-implement-refresh-token-with-httpinterceptor-bfa27b966f57
    AccessTokenInterceptor.prototype.intercept = function (request, next) {
        var _this = this;
        if (request.url.includes('auth')) {
            return next.handle(request);
        }
        else {
            var requestWithToken = request.clone({ headers: request.headers.set('token', this.authService.accessToken) });
            return next.handle(requestWithToken).pipe(Object(rxjs_operators__WEBPACK_IMPORTED_MODULE_4__["catchError"])(function (error, _) {
                if (error instanceof _angular_common_http__WEBPACK_IMPORTED_MODULE_3__["HttpErrorResponse"]) {
                    if (error.status == 401) {
                        return _this.authService.refresh(_this.authService.refreshToken).pipe(Object(rxjs_operators__WEBPACK_IMPORTED_MODULE_4__["switchMap"])(function (data, index) {
                            var requestWithToken = request.clone({ headers: request.headers.set('token', _this.authService.accessToken) });
                            return next.handle(requestWithToken);
                        }));
                    }
                    else {
                        _this.router.navigate(['login']);
                        return Object(rxjs__WEBPACK_IMPORTED_MODULE_0__["throwError"])(error);
                    }
                }
                else {
                    return Object(rxjs__WEBPACK_IMPORTED_MODULE_0__["throwError"])(error);
                }
            }));
        }
    };
    AccessTokenInterceptor = __decorate([
        Object(_angular_core__WEBPACK_IMPORTED_MODULE_1__["Injectable"])(),
        __metadata("design:paramtypes", [AuthService, _angular_router__WEBPACK_IMPORTED_MODULE_2__["Router"]])
    ], AccessTokenInterceptor);
    return AccessTokenInterceptor;
}());



/***/ }),

/***/ "./src/app/services/config.ts":
/*!************************************!*\
  !*** ./src/app/services/config.ts ***!
  \************************************/
/*! exports provided: apiRoot */
/***/ (function(module, __webpack_exports__, __webpack_require__) {

"use strict";
__webpack_require__.r(__webpack_exports__);
/* harmony export (binding) */ __webpack_require__.d(__webpack_exports__, "apiRoot", function() { return apiRoot; });
var apiRoot = 'https://farm.openzim.org';
// export let apiRoot: string = '';


/***/ }),

/***/ "./src/environments/environment.ts":
/*!*****************************************!*\
  !*** ./src/environments/environment.ts ***!
  \*****************************************/
/*! exports provided: environment */
/***/ (function(module, __webpack_exports__, __webpack_require__) {

"use strict";
__webpack_require__.r(__webpack_exports__);
/* harmony export (binding) */ __webpack_require__.d(__webpack_exports__, "environment", function() { return environment; });
// This file can be replaced during build by using the `fileReplacements` array.
// `ng build ---prod` replaces `environment.ts` with `environment.prod.ts`.
// The list of file replacements can be found in `angular.json`.
var environment = {
    production: false
};
/*
 * In development mode, to ignore zone related error stack frames such as
 * `zone.run`, `zoneDelegate.invokeTask` for easier debugging, you can
 * import the following file, but please comment it out in production mode
 * because it will have performance impact when throw error
 */
// import 'zone.js/dist/zone-error';  // Included with Angular CLI.


/***/ }),

/***/ "./src/main.ts":
/*!*********************!*\
  !*** ./src/main.ts ***!
  \*********************/
/*! no exports provided */
/***/ (function(module, __webpack_exports__, __webpack_require__) {

"use strict";
__webpack_require__.r(__webpack_exports__);
/* harmony import */ var _angular_core__WEBPACK_IMPORTED_MODULE_0__ = __webpack_require__(/*! @angular/core */ "./node_modules/@angular/core/fesm5/core.js");
/* harmony import */ var _angular_platform_browser_dynamic__WEBPACK_IMPORTED_MODULE_1__ = __webpack_require__(/*! @angular/platform-browser-dynamic */ "./node_modules/@angular/platform-browser-dynamic/fesm5/platform-browser-dynamic.js");
/* harmony import */ var _app_app_module__WEBPACK_IMPORTED_MODULE_2__ = __webpack_require__(/*! ./app/app.module */ "./src/app/app.module.ts");
/* harmony import */ var _environments_environment__WEBPACK_IMPORTED_MODULE_3__ = __webpack_require__(/*! ./environments/environment */ "./src/environments/environment.ts");




if (_environments_environment__WEBPACK_IMPORTED_MODULE_3__["environment"].production) {
    Object(_angular_core__WEBPACK_IMPORTED_MODULE_0__["enableProdMode"])();
}
Object(_angular_platform_browser_dynamic__WEBPACK_IMPORTED_MODULE_1__["platformBrowserDynamic"])().bootstrapModule(_app_app_module__WEBPACK_IMPORTED_MODULE_2__["AppModule"])
    .catch(function (err) { return console.log(err); });


/***/ }),

/***/ 0:
/*!***************************!*\
  !*** multi ./src/main.ts ***!
  \***************************/
/*! no static exports found */
/***/ (function(module, exports, __webpack_require__) {

module.exports = __webpack_require__(/*! /Volumes/Data/Developer/zimfarm/dispatcher/frontend/src/main.ts */"./src/main.ts");


/***/ })

},[[0,"runtime","vendor"]]]);
//# sourceMappingURL=main.js.map