export class User {
	username: string;
	isAdmin: boolean;

	constructor(username: string, isAdmin: boolean) {
		this.username = username;
		this.isAdmin = isAdmin;
	}
}