<template>
  <div id="app">
    <NavBar />
    <AlertFeedback />
    <router-view />
  </div>
</template>

<script type="text/javascript">
  import axios from 'axios'
  import moment from 'moment'
  import jwt from 'jsonwebtoken';

  import Constants from './constants.js'
  import ZimfarmMixins from './components/Mixins.js'
  import NavBar from './components/NavBar.vue'
  import AlertFeedback from './components/AlertFeedback.vue'

  export default {
    name: 'app',
    mixins: [ZimfarmMixins],
    components: {NavBar, AlertFeedback},
    methods: {
      tokenHasExpired() {
        let expiry = this.$store.getters.token_expiry;
        if (!expiry)
          return true;
        return moment().isAfter(expiry);
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

        let expiry = moment(token_data.payload.exp * 1000);
        if (moment().isAfter(expiry)) {
          this.fetchNewTokenFromRefresh(
            token_data.refresh_token,
            function () {},
            function () { // on error
              this.$cookie.delete(Constants.TOKEN_COOKIE_NAME);
            }
          );
        } else {
          this.$store.dispatch('saveAuthenticationToken', token_data);
        }
      },
      fetchNewTokenFromRefresh(refresh_token, on_success, on_error) {
        if (!refresh_token) {
          refresh_token = this.$store.getters.refresh_token;
        }

        if (!refresh_token) {
          if (on_error)
            on_error("no refresh-token");
          return;
        }

        let parent = this;
        let req_headers = parent.$root.axios.defaults.headers;
        req_headers['refresh-token'] = refresh_token;
        parent.queryAPI('post', '/auth/token', {}, {headers: req_headers})
          .then(function (response) {
            parent.handleTokenResponse(response);
            parent.alertInfo("Signed-in!", "Your token has been refreshed.");
            if (on_success)
              on_success(response);
          })
          .catch(function (error) {
            console.error(error);
            if (on_error)
              on_error(error);
          })
      },
      checkExpiryAndUpdateUI() {
        if (this.tokenHasExpired()) {
          // attempt to renew token using refresh one
          this.fetchNewTokenFromRefresh(
            null,
            function () {}, // on success
            function () {  // on error
              let msg = "Your token expired " + this.$store.getters.token_expiry.fromNow() + ". You can sign back in at any time.";
              this.$store.dispatch('clearAuthentication');
              this.$cookie.delete(Constants.TOKEN_COOKIE_NAME);
              this.alertInfo("Signed-out!", msg);
          }.bind(this));
        }
      },
      loadLanguages() {
        let parent = this;
        // download languages
        if (!parent.$store.getters.languages.length) {
          this.toggleLoader("fetching languages…");
          parent.queryAPI('get', '/languages/', {params: {limit: 400}})
            .then(function (response) {
              let languages = [];
              for (var i=0; i<response.data.items.length; i++){
                languages.push(response.data.items[i]);
              }
              parent.$store.dispatch('setLanguages', languages);
            })
            .catch(function (error) {
              parent.alertDanger("Unable to fecth languages",  Constants.standardHTTPError(error.response));
              return;
            }).then(function () {
              parent.toggleLoader(false);
            });
        }
      },
      loadTags() {
        let parent = this;
        // download tags
        if (!parent.$store.getters.tags.length) {
          this.toggleLoader("fetching tags…");
          parent.queryAPI('get', '/tags/', {params: {limit: 100}})
            .then(function (response) {
              let tags = [];
              for (var i=0; i<response.data.items.length; i++){
                tags.push(response.data.items[i]);
              }
              parent.$store.dispatch('setTags', tags);
            })
            .catch(function (error) {
              parent.alertDanger("Unable to fecth tags", Constants.standardHTTPError(error.response));
              return;
            }).then(function () {
              parent.toggleLoader(false);
            });
        }
      },
      loadOffliners() {
        let parent = this;
        // download offliners
        if (!parent.$store.getters.offliners.length) {
          this.toggleLoader("fetching offliners…");
          parent.queryAPI('get', '/offliners/', {params: {limit: 100}})
            .then(function (response) {
              let offliners = [];
              for (var i=0; i<response.data.items.length; i++){
                offliners.push(response.data.items[i]);
              }
              parent.$store.dispatch('setOffliners', offliners);
              parent.loadOfflinersDefs();
            })
            .catch(function (error) {
              parent.alertDanger("Unable to fecth offliners", Constants.standardHTTPError(error.response));
              return;
            }).then(function () {
              parent.toggleLoader(false);
            });
        }
      },
      async loadOfflinersDefs() {
        let parent = this;
        // download offliners defs
        if (!parent.$store.getters.offliners_defs.length) {
          this.toggleLoader("fetching offliners defs…");

          let requests = parent.$store.getters.offliners.map(function (offliner) {
            return parent.queryAPI('get', '/offliners/' + offliner);
          });
          let results = await axios.all(requests);
          let definitions = {};
          parent.$store.getters.offliners.forEach(function (offliner, index) {
            definitions[offliner] = results[index].data;
          });
          parent.$store.dispatch('setOfflinersDefs', definitions);
        }
      },
      loadMetaData() {  // load languages and tags metadata from API then launch loadSchedules
        this.loadLanguages();
        this.loadTags();
        this.loadOffliners();
      },
      loadSchedule(schedule_name, force_reload, on_success, on_error) {
        if (!force_reload && this.$store.getters.schedule && this.$store.getters.schedule.name == schedule_name){
          if (on_success) { on_success(); }
          return;
        }

        let parent = this;

        parent.$store.dispatch('clearSchedule');  // reset until we receive the right schedule
        parent.toggleLoader("fetching schedule…");
        parent.queryAPI('get', '/schedules/' + schedule_name)
          .then(function (response) {
              // parent.error = null;
              let schedule = response.data;
              parent.$store.dispatch('setSchedule', schedule);

              if (on_success) { on_success(); }
          })
          .catch(function (error) {
            if (on_error) { on_error(Constants.standardHTTPError(error.response)); }
          })
          .then(function () {
              parent.toggleLoader(false);
          });
      }
    },
    beforeMount() {
      this.loadTokenFromCookie();
      this.$root.$on('load-schedule', this.loadSchedule);
    },
    mounted() {
      this.loadMetaData();
    },
    watch: {
      $route() {
        this.checkExpiryAndUpdateUI();
      },
    },
  }
</script>
