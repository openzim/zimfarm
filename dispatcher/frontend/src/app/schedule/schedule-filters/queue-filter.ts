import { Component, AfterViewInit } from '@angular/core';
import { FormBuilder, FormGroup, FormControl, FormArray } from '@angular/forms';
import { AgFilterComponent } from 'ag-grid-angular';
import { IFilterParams, IDoesFilterPassParams } from 'ag-grid-community';
import { queues } from '../../services/entities';

@Component({
    templateUrl: './queue-filter.html'
})
export class QueueFilterComponent implements AgFilterComponent {
    form: FormGroup;
    params: IFilterParams;
    hidePopup?: Function;
    selectedQueues: string[];

    constructor(private formBuilder: FormBuilder) {
        this.selectedQueues = [];
        let controls = this.getQueues().map(_ => new FormControl(false));
        this.form = this.formBuilder.group({queues: new FormArray(controls)})
    }

    getQueues() { return queues; }

    onSubmit() {
        this.selectedQueues = this.form.value.queues
            .map((value, index) => value ? this.getQueues()[index] : null)
            .filter(value => value !== null);
        this.params.filterChangedCallback();
        this.hidePopup();
    }

    agInit(params: IFilterParams) {
        this.params = params;
    }

    isFilterActive(): boolean {
        return this.selectedQueues.length > 0;
    }

    doesFilterPass(params: IDoesFilterPassParams): boolean {
        return true;
    }

    getModel(): any {
        return this.selectedQueues;
    }

    setModel(model: any) {
        this.selectedQueues = model;
    }

    applyToAll(value: boolean): any {
    	this.form['controls'].queues['controls'].forEach(function (item, i) {
    		item.setValue(value);
    	});
    }

    afterGuiAttached(params?: {hidePopup?: Function}) {
        this.hidePopup = params.hidePopup;
    }
}
