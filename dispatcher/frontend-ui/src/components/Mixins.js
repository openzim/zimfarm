
import moment from 'moment';
import jwt from 'jsonwebtoken';

import Constants from '../constants.js'

export default {
  data() {
    return {
      selectedLimit: this.getLimitPreference(), // user-defined nb of tasks to retrieve/display
      limits: Constants.LIMIT_CHOICES,
     };
  },
  computed: {
    publicPath() { return process.env.BASE_URL; },  // for static files linking
    categories() { return Constants.categories; }, // list of categories for filter/edit
    warehouse_paths() { return Constants.warehouse_paths; },  // list of paths for edit
    periodicities() { return Constants.periodicities; },  // list of paths for edit
    languages() { return this.$store.getters.languages; },  // list of lang for filter/edit
    tags() { return this.$store.getters.tags; },  // list of tags for filter/edit
    offliners() { return this.$store.getters.offliners; }, // list of offliners for edit

    isLoggedIn() {
      try {
        return Boolean(this.$store.getters.username !== null && !this.token_expired);
      } catch { return false; }
    },
    token_expired() {
      let expiry = this.$store.getters.token_expiry;
      return (!expiry) ? true : moment().isAfter(expiry);
    },
    canRequestTasks() { return this.$root.has_perm("tasks", "request"); },
    canUnRequestTasks() { return this.$root.has_perm("tasks", "unrequest"); },
    canCancelTasks() { return this.$root.has_perm("tasks", "cancel"); },
    canCreateSchedules() { return this.$root.has_perm("schedules", "create"); },
    canUpdateSchedules() { return this.$root.has_perm("schedules", "update"); },
    canDeleteSchedules() { return this.$root.has_perm("schedules", "delete"); },
    canReadUsers() { return this.$root.has_perm("users", "read"); },
    canSSHKeyUsers() { return this.$root.has_perm("users", "ssh_keys"); },
    canCreateUsers() { return this.$root.has_perm("users", "create"); },
    canUpdateUsers() { return this.$root.has_perm("users", "update"); },
    canDeleteUsers() { return this.$root.has_perm("users", "delete"); },
    canChangePasswordUsers() { return this.$root.has_perm("users", "change_password"); },
    
  },
  methods: {
    scrollToTop() { window.scrollTo(0,0); },
    format_dt(dt) { return Constants.format_dt(dt); },
    from_now(dt) { return Constants.from_now(dt); },
    toggleLoader(text) { // shortcut to store's loader status changer
      let payload = text ? {status: true, text: text} : {status: false};
      this.$store.dispatch('setLoading', payload);
    },
    getLimitPreference() {   // retrieve nb of items to display from cookie
      return this.$cookie.get('pref-limit') || Constants.DEFAULT_LIMIT;
    },
    saveLimitPreference(value) {  // save nb of items to display in a cookie
      this.$cookie.set('pref-limit', value);
    },

    redirectTo(name, params) {
      let route_entry = {name: name};
      if (params)
        route_entry.params = params;
      this.$router.push(route_entry);
    },

    confirmAction(action, onConfirm, onRefuse, onError) {
      let options = {
        title: "Please Confirm",
        size: "sm",
        buttonSize: 'sm',
        okVariant: 'danger',
        okTitle: 'YES',
        cancelTitle: 'NO',
        centered: true
      };
      this.$bvModal.msgBoxConfirm("Do you want to " + action + "?", options)
        .then(value => {
          if (value === true && onConfirm) {
            onConfirm();
          }
          if (value === false && onRefuse){
            onRefuse();
          }
        })
        .catch(err => {
          if (onError){
            onError(err);
          }
        });
    },

    alert(level, title, text, duration) {
      let message = "<strong>" + title + "</strong>";
      if (text)
        message += "<br />" + text;
      this.$root.$emit('feedback-message', level, message, duration);
    },
    alertInfo(title, text, duration) { this.alert('info', title, text, duration); },
    alertSuccess(title, text, duration) { this.alert('success', title, text, duration); },
    alertWarning(title, text, duration) { this.alert('warning', title, text, duration); },
    alertDanger(title, text, duration) { this.alert('danger', title, text, duration); },
    alertAccessRefused(perm_name) { this.alertWarning("Access Refused", "You don't have <code>" + perm_name + "</code> permission."); },
    alertError(text) { this.alertDanger("Error", text, Constants.ALERT_PERMANENT_DURATION); },

    statusClass(status) {
      if (status == 'succeeded')
        return 'schedule-suceedeed';
      if (["failed", "canceled", "cancel_requested"].indexOf(status))
        return 'schedule-failed';
      return 'schedule-running';
    },
    handleTokenResponse(response) {
      console.debug("handleTokenResponse", response);
      // prepare our token structure
      let access_token = response.data.access_token;
      let refresh_token = response.data.refresh_token;
      let token_data = {
        access_token: access_token,
        payload: jwt.decode(access_token),
        refresh_token: refresh_token,
      }
      // save token to store
      this.$store.dispatch('saveAuthenticationToken', token_data);

      // save to cookie
      let cookie_data = {"access_token": access_token, "refresh_token": refresh_token};
      this.$cookie.set(Constants.TOKEN_COOKIE_NAME,
                       JSON.stringify(cookie_data),
                       {expires: Constants.TOKEN_COOKIE_EXPIRY,
                        secure: Constants.isProduction()});
    },
    async renew_token_from_refresh(refresh_token, on_success, on_error) {
      console.debug("renew_token_from_refresh", refresh_token);
      if (refresh_token === null)
        refresh_token = this.$store.getters.refresh_token;

      let req_headers = this.$root.axios.defaults.headers;
      req_headers['refresh-token'] = refresh_token;

      let response;
      try {
        response = await this.$root.axios.post('/auth/token', {}, {headers: req_headers});
        console.debug("/auth/token success");
        console.debug(response);
      } catch (error) {
        console.debug("/auth/token failure");
        response = null;
        console.error(error);
      }

      if (response) {
        this.handleTokenResponse(response);
        this.alertInfo("Signed-in!", "Your token has been refreshed.");

        if (on_success) {
          on_success();
        }
      } else {
        if (on_error) {
          on_error();
        }
      }
    },
    loadTokenFromCookie() {
      // already authenticated
      if (this.isLoggedIn)
        return;
      let cookie_value = this.$cookie.get(Constants.TOKEN_COOKIE_NAME);

      // no cookie
      if (!cookie_value)
        return;

      let token_data;
      try {
         token_data = JSON.parse(cookie_value);
         token_data.payload = jwt.decode(token_data.access_token);
      } catch {
        // incorrect cookie payload
        this.$cookie.delete(Constants.TOKEN_COOKIE_NAME);
        return;
      }

      console.debug("found auth cookie");

      let expiry = moment(token_data.payload.exp * 1000);
      let parent = this;
      if (moment().isAfter(expiry)) {
        console.debug("cookie token expired");

        this.renew_token_from_refresh(
          token_data.refresh_token,
          function () { console.debug("could renew the token, great!");},
          function () {
            console.debug("couldnt refresh token, removing cookie");
            parent.$cookie.delete(Constants.TOKEN_COOKIE_NAME);
          }
        );
      } else {
        console.log("cookie token not expired, using it.");
        this.$store.dispatch('saveAuthenticationToken', token_data);
      }
    },
    queryAPI(method, path, data, config) {
      console.debug("queryAPI", method, path);
      if (data === undefined)
        data = {};
      if (config === undefined)
        config = {};

      if (this.token_expired && this.$store.getters.access_token) {
        console.debug("we have an expired token, attempting to refresh before request.");

        let parent = this;
        return new Promise(function (resolve) {
          parent.renew_token_from_refresh(
            null,
            function () {
              console.debug("renewed the token! executing query");
              resolve(parent.$root.axios[method](path, data, config));
            },
            function () {
              resolve(parent.$root.axios[method](path, data, config));
            }
          );
        });
      } else {
        // returning straight request/promise
        return this.$root.axios[method](path, data, config);
      }
    },
  }
}
