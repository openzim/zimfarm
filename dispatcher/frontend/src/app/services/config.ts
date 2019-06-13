
export function getAPIRoot(): string {
    let root = window.location.origin;
    if (root.includes('localhost')) {
        root = 'https://farm.openzim.org';
    }
    return root + '/api';
}

export function getWareHouseLogsUrl(): string {
    return 'https://logs.warehouse.farm.openzim.org';
}
