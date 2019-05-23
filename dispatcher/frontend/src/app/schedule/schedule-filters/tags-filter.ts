import { Component, AfterViewInit } from '@angular/core';
import { FormBuilder, FormGroup, FormControl, FormArray } from '@angular/forms';
import { AgFilterComponent } from 'ag-grid-angular';
import { IFilterParams, IDoesFilterPassParams } from 'ag-grid-community';
import { queues } from '../../services/entities';

@Component({
    templateUrl: './tags-filter.html'
})
export class TagsFilterComponent implements AgFilterComponent {
    form: FormGroup;
    params: IFilterParams;
    hidePopup?: Function;
    _tags: string = "";  // ngModel comma-separated string
    tags: string[] = []; // list of tags to forward

    constructor(private formBuilder: FormBuilder) {
    }

    onSubmit() {
        this.setModel(this._tags);
        this.params.filterChangedCallback();
        this.hidePopup();
    }

    onReset(): void {
        this._tags = "";
        this.setModel(this._tags);
    }

    agInit(params: IFilterParams) {
        this.params = params;
    }

    isFilterActive(): boolean {
        return this._tags.length > 0;
    }

    doesFilterPass(params: IDoesFilterPassParams): boolean {
        return true;
    }

    getModel(): any {
        return this.tags;
    }

    setModel(model: any) {
        this.tags = model.split(",").map(x => x.trim()).filter(x => x.length > 0);
    }

    afterGuiAttached(params?: {hidePopup?: Function}) {
        this.hidePopup = params.hidePopup;
    }
}
