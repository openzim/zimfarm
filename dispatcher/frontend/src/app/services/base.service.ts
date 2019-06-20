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
