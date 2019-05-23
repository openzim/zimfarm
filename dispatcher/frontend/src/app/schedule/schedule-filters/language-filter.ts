import { Component, AfterViewInit } from '@angular/core';
import { FormBuilder, FormGroup, FormControl, FormArray } from '@angular/forms';
import { AgFilterComponent } from 'ag-grid-angular';
import { IFilterParams, IDoesFilterPassParams } from 'ag-grid-community';
import { LanguagesService } from '../../services/languages.service';

@Component({
    templateUrl: './language-filter.html'
})
export class LanguageFilterComponent implements AgFilterComponent {
    form: FormGroup;
    params: IFilterParams;
    hidePopup?: Function;
    selectedLanguages: string[];
    initialized: boolean = false;

    constructor(private formBuilder: FormBuilder,
    			private languagesService:LanguagesService) {
    	this.selectedLanguages = [];
        let controls = this.getLanguages().map(_ => new FormControl(false));
        this.form = this.formBuilder.group({languages: new FormArray(controls)})
    }

    getLanguages(): Array<string> {
    	return this.languagesService.lang_codes;
    }

    onSubmit() {
        this.selectedLanguages = this.form.value.languages
            .map((value, index) => value ? this.getLanguages()[index] : null)
            .filter(value => value !== null);
        this.params.filterChangedCallback();
        this.hidePopup();
    }

    agInit(params: IFilterParams) {
        this.params = params;
    }

    isFilterActive(): boolean {
        return this.selectedLanguages.length > 0;
    }

    doesFilterPass(params: IDoesFilterPassParams): boolean {
        return true;
    }

    getModel(): any {
        return this.selectedLanguages;
    }

    setModel(model: any) {
        this.selectedLanguages = model;
    }

    languageName(lang_code): string {
    	return this.languagesService.getEnglishName(lang_code);
    }

    applyToAll(value: boolean): any {
    	this.form['controls'].languages['controls'].forEach(function (item, i) {
    		item.setValue(value);
    	});
    }

    afterGuiAttached(params?: {hidePopup?: Function}) {
        this.hidePopup = params.hidePopup;
    }
}
