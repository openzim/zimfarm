<!-- Change Password Page

  - gets curent and new password
  - send to API
  - handles own login/error -->

<template>
  <div class="container text-center">
    <form class="form-signin" @submit.prevent="changePassword">
      <h1 class="h3 mb-3 font-weight-normal">Password Change</h1>
      <input type="password" class="form-control top-field" v-model="current_password" placeholder="Current Password" required autofocus>
      <input type="password" class="form-control bottom-field" v-model="new_password" placeholder="New Password" required>
      <p class="alert alert-danger text-left" v-show="error" v-html="error" />
      <p class="alert alert-warning text-left" v-show="working">
        <font-awesome-icon icon="spinner" size="lg" spin /> changing your password…
      </p>
      <button class="btn btn-lg btn-primary btn-block" type="submit" v-show="shouldDisplayButton">Update Password</button>
      <p class="mt-5 mb-3 text-muted"><a :href="'mailto:' + contact_email">{{ contact_email }}</a></p>
    </form>
  </div>
</template>

<script type="text/javascript">
  import Constants from '../constants.js'
  import ZimfarmMixins from '../components/Mixins.js'

  export default {
    name: 'ChangePassword',
    mixins: [ZimfarmMixins],
    data() {
      return {
        current_password: null, // user's username
        new_password: null, // users's password
        working: false, // own-loader toggle
        error: null, // own-error-message
      };
    },
    methods: {
      changePassword() { // request token on API using credentials
        let parent = this;

        if (!parent.$store.getters.username) {
          parent.error = "<strong>Refused</strong>: You must be signed-in to change your password…";
          return;
        }

        parent.working = true;
        parent.error = null;

        let payload = {current: parent.current_password, new: parent.new_password};
        parent.queryAPI('patch', '/users/' + parent.$store.getters.username + '/password', payload)
          .then(function () {
              parent.alertSuccess("Changed!", "Your password has been updated.");
              parent.$router.back();  // redirect
            })
            .catch(function (error) {
              parent.error = Constants.standardHTTPError(error.response);
            })
            .then(function () {
              parent.working = false;
            });
        }
    },
    computed: {
      contact_email() { return Constants.contact_email; },
      shouldDisplayButton() { // whether to display Sign-in button
        return !this.working;
      },
    },
    beforeMount() { // redirect to SignIn if not logged-in
      if (!this.isLoggedIn)
        this.redirectTo('sign-in');
    },
  }
</script>

<style type="text/css" scoped>
  .form-signin {
    width: 100%;
    max-width: 330px;
    padding: .5rem;
    margin: auto;
  }
  .form-signin .form-control {
    position: relative;
    box-sizing: border-box;
    height: auto;
    padding: .5rem;
    font-size: 16px;
  }
  .form-signin .form-control:focus {
    z-index: 2;
  }
  .form-signin .top-field {
    margin-bottom: -1px;
    border-bottom-right-radius: 0;
    border-bottom-left-radius: 0;
  }
  .form-signin .bottom-field {
    margin-bottom: 10px;
    border-top-left-radius: 0;
    border-top-right-radius: 0;
  }
</style>
