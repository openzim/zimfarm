export class BaseService {
    getAPIRoot(): string {
        let root = window.location.origin;
        if (root.includes('localhost')) {
            root = 'https://farm.openzim.org';
        }
        return root + '/api';
    }
    getWareHouseLogsUrl(): string {
        return 'https://logs.warehouse.farm.openzim.org';
    }
}

export class BaseInput<T> {
    value: T;
    key: string;
    label: string;
    required: boolean;
    order: number;
    controlType: string;
   
    constructor(options: {
        value?: T,
        key?: string,
        label?: string,
        required?: boolean,
        order?: number,
        controlType?: string
    } = {}) {
        this.value = options.value;
        this.key = options.key || '';
        this.label = options.label || '';
        this.required = !!options.required;
        this.order = options.order === undefined ? 1 : options.order;
        this.controlType = options.controlType || '';
    }
}

export class TextFieldInput extends BaseInput<string> {
    controlType = 'textbox';
    type: string;
  
    constructor(options: {} = {}) {
        super(options);
        this.type = options['type'] || '';
    }
}