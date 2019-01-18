import { NgModule, Pipe, PipeTransform } from '@angular/core';
import { CommonModule } from '@angular/common';

import cronstrue from 'cronstrue';
import { TimeAgoPipe } from 'time-ago-pipe';

import { Beat } from '../services/schedules.service';

@Pipe({name: 'beatDescription'})
export class BeatDescription implements PipeTransform {
    transform(beat: Beat) {
        if (beat.type == 'crontab') {
            let config = beat.config;
            let cron = Array(config['minute'], config['hour'], config['day_of_month'], config['month_of_year'], config['day_of_week']).join(' ');
            return cronstrue.toString(cron);
        } else {
            return 'Error: unsupported beat type';
        }
    }
}

@NgModule({
    imports: [CommonModule],
    declarations: [
        TimeAgoPipe,
        BeatDescription
    ],
    exports: [
        TimeAgoPipe,
        BeatDescription
    ]
})
export class SharedModule { }

