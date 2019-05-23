import { Injectable } from '@angular/core';
import { languages } from './entities';

export interface Language {
    code: string;
    name_en: string;
    name_native: string;
}

@Injectable({
    providedIn: 'root',
})
export class LanguagesService {

    lang_codes: Array<string> = [];
    lang_names: Array<string> = [];

    constructor() {
        languages.forEach((item) => {
            this.lang_codes.push(item.code);
            this.lang_names.push(item.name_en);
        });
    }

    all(): Array<Language> {
        return languages;
    }

    getEnglishName(lang_code: string): string {
        let pos = this.lang_codes.indexOf(lang_code);
        if (pos < 0) {
            return lang_code;    
        }
        return this.lang_names[pos];
    }
}


