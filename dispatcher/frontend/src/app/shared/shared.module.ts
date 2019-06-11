import { NgModule, Pipe, PipeTransform } from '@angular/core';
import { CommonModule } from '@angular/common';

import cronstrue from 'cronstrue';
import { TimeAgoPipe } from 'time-ago-pipe';

@NgModule({
    imports: [CommonModule],
    declarations: [
        TimeAgoPipe,
    ],
    exports: [
        TimeAgoPipe,
    ]
})
export class SharedModule { }

