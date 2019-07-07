import { Injectable } from '@angular/core';

import { BaseService } from './base.service';

@Injectable({
    providedIn: 'root',
})
export class ConfigService extends BaseService {
    categories: Category[] = [
        {'name': 'Wikipedia', 'code': 'wikipedia'},
        {'name': 'Wikibooks', 'code': 'wikibooks'},
        {'name': 'Wikinews', 'code': 'wikinews'},
        {'name': 'Wikiquote', 'code': 'wikiquote'},
        {'name': 'Wikisource', 'code': 'wikisource'},
        {'name': 'Wikispecies', 'code': 'wikispecies'},
        {'name': 'Wikiversity', 'code': 'wikiversity'},
        {'name': 'Wikivoyage', 'code': 'wikivoyage'},
        {'name': 'Wiktionary', 'code': 'wiktionary'},
        {'name': 'Vikidia', 'code': 'vikidia'},
        {'name': 'TED', 'code': 'ted'},
        {'name': 'Stack Exchange', 'code': 'stack_exchange'},
        {'name': 'Psiram', 'code': 'psiram'},
        {'name': 'Phet', 'code': 'phet'},
        {'name': 'Gutenberg', 'code': 'gutenberg'},
        {'name': 'Other', 'code': 'other'},
    ]
}

export class Category {
    name: string
    code: string
}