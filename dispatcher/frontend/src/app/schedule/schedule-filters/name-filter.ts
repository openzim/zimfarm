import { Component } from '@angular/core';
import { AgFilterComponent } from 'ag-grid-angular';
import { IFilterParams, IDoesFilterPassParams } from 'ag-grid-community';
import { queues } from '../../services/entities';

@Component({
    templateUrl: './name-filter.html'
})
export class NameFilterComponent implements AgFilterComponent {
    params: IFilterParams;
    hidePopup?: Function;
    name: string = "";

    getQueues() { return queues; }

    onSubmit() {
        this.params.filterChangedCallback();
        this.hidePopup();
    }

    onReset(): void {
        this.name = "";
    }

    agInit(params: IFilterParams) {
        this.params = params;
    }

    isFilterActive(): boolean {
        return this.name.length > 0;
    }

    doesFilterPass(params: IDoesFilterPassParams): boolean {
        return true;
    }

    getModel(): any {
        return this.name;
    }

    setModel(model: any) {
        this.name = model;
    }

    afterGuiAttached(params?: {hidePopup?: Function}) {
        this.hidePopup = params.hidePopup;
    }
}
