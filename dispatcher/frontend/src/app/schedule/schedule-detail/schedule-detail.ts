import { Component, OnInit } from '@angular/core';
import { FormBuilder, FormControl, FormGroup } from '@angular/forms';
import { ActivatedRoute } from '@angular/router';
import { Observable } from 'rxjs';
import { switchMap } from 'rxjs/operators';

import { Schedule, SchedulesService } from '../../services/schedules.service';
import { BaseInput } from 'src/app/services/base.service';


@Component({
    templateUrl: './schedule-detail.html',
    styleUrls: ['./schedule-detail.css']
})
export class ScheduleDetailComponent implements OnInit {
    schedule$: Observable<Schedule>;
    imageForm = new FormGroup({
        name: new FormControl(''),
        tag: new FormControl('')
    });
    offlinerFlagsForm = new FormGroup({});
    offlinerFlags: BaseInput<any>[] = [];

    constructor(
        private route: ActivatedRoute, 
        private schedulesService: SchedulesService) {}

    ngOnInit() {
        this.schedule$ = this.route.paramMap.pipe(
            switchMap(params => {
                return this.schedulesService.get(params.get('id_or_name'));
            })
        )

        let mwofflinerConfigs = [
            new BaseInput({key: 'mwUrl', required: true}),
            new BaseInput({key: 'adminEmail', required: true}),
            new BaseInput({key: 'articleList'}),
            new BaseInput({key: 'cacheDirectory'}),
            new BaseInput({key: 'customZimFavicon'}),
            new BaseInput({key: 'customZimTitle'}),
            new BaseInput({key: 'customZimDescription'}),
            new BaseInput({key: 'customZimTags'}),
            new BaseInput({key: 'customMainPage'}),
            new BaseInput({key: 'filenamePrefix'}),
            new BaseInput({key: 'format'}),
            new BaseInput({key: 'keepEmptyParagraphs'}),
            new BaseInput({key: 'keepHtml'}),
            new BaseInput({key: 'mwWikiPath'}),
            new BaseInput({key: 'mwApiPath'}),
            new BaseInput({key: 'mwModulePath'}),
            new BaseInput({key: 'mwDomain'}),
            new BaseInput({key: 'mwUsername'}),
            new BaseInput({key: 'mwPassword'}),
            new BaseInput({key: 'minifyHtml'}),
            new BaseInput({key: 'outputDirectory'}),
            new BaseInput({key: 'publisher'}),
            new BaseInput({key: 'redis'}),
            new BaseInput({key: 'requestTimeout'}),
            new BaseInput({key: 'resume'}),
            new BaseInput({key: 'useCache'}),
            new BaseInput({key: 'skipCacheCleaning'}),
            new BaseInput({key: 'speed'}),
            new BaseInput({key: 'verbose'}),
            new BaseInput({key: 'withoutZimFullTextIndex'}),
            new BaseInput({key: 'addNamespaces'}),
            new BaseInput({key: 'getCategories'}),
            new BaseInput({key: 'noLocalParserFallback'}),
        ];
        this.schedule$.subscribe(schedule => {
            if (schedule.config.image.name == 'openzim/mwoffliner') {
                this.offlinerFlagsForm = this.makeFormGroup(mwofflinerConfigs)
                this.offlinerFlags = mwofflinerConfigs
            } else {
                this.offlinerFlagsForm = this.makeFormGroup([])
                this.offlinerFlags = []
            }

            this.imageForm.patchValue(schedule.config.image);
            this.offlinerFlagsForm.patchValue(schedule.config.flags);
        })
    }

    onSubmit(schedule) {
        console.log('submit buttion is clicked.', schedule)
    }

    makeFormGroup(flags: BaseInput<any>[]): FormGroup {
        let group = {}
        flags.forEach(config => {
            group[config.key] = new FormControl()
        })
        return new FormGroup(group)
    }
}