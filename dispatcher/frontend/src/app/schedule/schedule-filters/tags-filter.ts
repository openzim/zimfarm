import { Component, AfterViewInit } from '@angular/core';
import { FormBuilder, FormGroup, FormControl, FormArray } from '@angular/forms';
import { AgFilterComponent } from 'ag-grid-angular';
import { IFilterParams, IDoesFilterPassParams } from 'ag-grid-community';
import { TagsService } from '../../services/tags.service';

@Component({
    templateUrl: './tags-filter.html'
})
export class TagsFilterComponent implements AgFilterComponent {
    form: FormGroup;
    params: IFilterParams;
    hidePopup?: Function;
    all_tags: string[] = [];
    selectedTags: string[] = [];
    initialized: boolean = false;

    constructor(private formBuilder: FormBuilder,
                private TagsService:TagsService) {
        let controls = this.getTags().map(_ => new FormControl(false));
        this.form = this.formBuilder.group({tags: new FormArray(controls)})
    }

    getTags(): Array<string> {
        return this.all_tags;
    }

    onSubmit() {
        this.selectedTags = this.form.value.tags
            .map((value, index) => value ? this.getTags()[index] : null)
            .filter(value => value !== null);
        this.params.filterChangedCallback();
        this.hidePopup();
    }

    agInit(params: IFilterParams) {
        this.params = params;
    }

    ngOnInit() {
        this.TagsService.fetch().subscribe(data => {
            this.all_tags = data.items;
            let controls = this.getTags().map(_ => new FormControl(false));
            this.form = this.formBuilder.group({tags: new FormArray(controls)})
        })
    }

    isFilterActive(): boolean {
        return this.selectedTags.length > 0;
    }

    doesFilterPass(params: IDoesFilterPassParams): boolean {
        return true;
    }

    getModel(): any {
        return this.selectedTags;
    }

    setModel(model: any) {
        this.selectedTags = model;
    }

    applyToAll(value: boolean): any {
        this.form['controls'].tags['controls'].forEach(function (item, i) {
            item.setValue(value);
        });
    }

    afterGuiAttached(params?: {hidePopup?: Function}) {
        this.hidePopup = params.hidePopup;
    }
}
