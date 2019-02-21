import { Component, AfterViewInit } from '@angular/core';
import { FormBuilder, FormGroup, FormControl, FormArray } from '@angular/forms';
import { AgFilterComponent } from 'ag-grid-angular';
import { IFilterParams, IDoesFilterPassParams } from 'ag-grid-community';


@Component({
    templateUrl: './category-filter.html'
})
export class CategoryFilterComponent implements AgFilterComponent {
    form: FormGroup;
    params: IFilterParams;
    hidePopup?: Function;
    categories = [
        'wikipedia', 'wikibooks', 'wikinews', 'wikiquote', 
        'wikisource', 'wikiversity', 'wikivoyage', 'wiktionary'];
    selectedCategories: string[];

    constructor(private formBuilder: FormBuilder) {
        this.selectedCategories = this.categories;
        let controls = this.categories.map(_ => new FormControl(true));
        this.form = this.formBuilder.group({categories: new FormArray(controls)})
    }

    onSubmit() {
        this.selectedCategories = this.form.value.categories
            .map((value, index) => value ? this.categories[index] : null)
            .filter(value => value !== null);
        this.params.filterChangedCallback();
        this.hidePopup();
    }

    agInit(params: IFilterParams) {
        this.params = params;
    }

    isFilterActive(): boolean {
        return this.selectedCategories.length > 0;
    }

    doesFilterPass(params: IDoesFilterPassParams): boolean {
        return true;
    }

    getModel(): any {
        return this.selectedCategories;
    }

    setModel(model: any) {
        this.selectedCategories = model;
    }

    afterGuiAttached(params?: {hidePopup?: Function}) {
        this.hidePopup = params.hidePopup;
    }
}