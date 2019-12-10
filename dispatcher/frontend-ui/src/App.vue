<template>
  <div id="app">
    <NavBar />
    <AlertFeedback />
    <router-view />
  </div>
</template>

<script type="text/javascript">
  import moment from 'moment';

  import NavBar from './components/NavBar.vue'
  import AlertFeedback from './components/AlertFeedback.vue'

  export default {
    name: 'app',
    components: {NavBar, AlertFeedback},

    methods: {
      loadTokenFromCookie() {
        // already authenticated
        if (this.$store.getters.username)
          return;
        let cookie_token = this.$cookie.get('token_data');

        // no cookie
        if (!cookie_token)
          return;

        let token_data;
        try {
           token_data = JSON.parse(cookie_token);
        } catch {
          // incorrect cookie payload
          this.$cookie.delete('token_data');
          return;
        }

        let expiry = moment(token_data.expires_on);
        if (moment().isAfter(expiry)) {
          this.$cookie.delete('token_data');
          return;
        }

        this.$store.dispatch('saveAuthenticationToken', token_data)
      },
      checkExpiryAndUpdateUI() {
        if (this.$store.getters.token_expired) {
          console.debug("token has expired, logging-out");
          let msg = "Your token expired " + this.$store.getters.token_expiry.fromNow() + ". You can sign back in at any time.";
          this.$store.dispatch('clearAuthentication');
          this.$root.$emit('feedback-message', 'info', "<strong>Signed-out!</strong><br />" + msg);
        }

      },
    },
    beforeMount() {
      this.loadTokenFromCookie();
    },
    watch: {
      $route() {
        this.checkExpiryAndUpdateUI();
      },
    },
  }
</script>
