<!-- Authentication Page

  - gets username and password
  - athenticates on the API
  - retrieve and store token in store
  - handles own login/error
  - save token info in cookie if asked to remember -->

<template>
  <div class="container text-center">
    <form class="form-signin" @submit.prevent="authenticate">
      <img :src="publicPath + 'assets/logo.svg'" />
      <h1 class="h3 mb-3 font-weight-normal">Please sign in</h1>
      <input type="text" class="form-control top-field" v-model="username" placeholder="Username" required autofocus>
      <input type="password" class="form-control bottom-field" v-model="password" placeholder="Password" required>
      <div class="checkbox mb-3 text-left">
        <label>
          <input type="checkbox" v-model="remember"> Remember me
        </label>
      </div>
      <p class="alert alert-danger text-left" v-show="error">{{ error }}</p>
      <p class="alert alert-warning text-left" v-show="working">
        <font-awesome-icon icon="spinner" size="lg" spin /> signing you in…
      </p>
      <button class="btn btn-lg btn-primary btn-block" type="submit" v-if="shouldDisplayButton">Sign in</button>
      <p class="mt-5 mb-3 text-muted"><a :href="'mailto:' + contact_email">{{ contact_email }}</a></p>
    </form>
  </div>
</template>

<script type="text/javascript">
  import moment from 'moment';

  import Constants from '../constants.js'
  import ZimfarmMixins from '../components/Mixins.js'

  export default {
    name: 'SignIn',
    mixins: [ZimfarmMixins],
    data() {
      return {
        username: null, // user's username
        password: null, // users's password
        remember: true, // whether to record result in cookie
        working: false, // own-loader toggle
        error: null, // own-error-message
      };
    },
    computed: {
      contact_email() { return Constants.contact_email; },
      shouldDisplayButton() { // whether to display Sign-in button
        return !this.working;
      }
    },
    methods: {
      authenticate() { // request token on API using credentials
        let parent = this;

        parent.working = true;
        parent.error = null;

        let now = moment();
        let expires_on = moment();
        let payload = {username: this.username, password: this.password};

        parent.$root.axios.post('/auth/authorize', Constants.params_serializer(payload))
          .then(function (response) {
              // prepare our token structure
              expires_on.add(response.data.expires_in, 'seconds');
              let token_data = {
                username: parent.username,
                access_token: response.data.access_token,
                authenticated_on: now.toDate(),
                expires_on: expires_on.toDate(),
                refresh_token: response.data.refresh_token
              }
              // save token to store
              parent.$store.dispatch('saveAuthenticationToken', token_data)
              // save to cookie
              parent.$cookie.set('token_data', JSON.stringify(token_data), {expires: '1h'});
              // redirect
              parent.$router.back();
            })
            .catch(function (error) {
              parent.error = Constants.standardHTTPError(error.response);
            })
            .then(function () {
              parent.working = false;
            });
        }
    },
  }
</script>
