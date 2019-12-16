<!-- Sign-in button that transforms into a user menu
  - send to sign-in if not logged-in
  - copy token to clipboard
  - send to change-password (TBI)
  - log-out -->

<template2>
  <span v-if="$store.getters.username" class="nav-item dropdown">
    <a class="dropdown-toggle btn btn-sm btn-light"
       href="#" id="userdropdown"
       data-toggle="dropdown"
       aria-haspopup="true"
       aria-expanded="false">
       <font-awesome-icon icon="user-circle" size="sm" /> {{ $store.getters.username }}
     </a>
    <div class="dropdown-menu dropdown-menu-right" aria-labelledby="userdropdown">
      <button class="dropdown-item" @click.prevent="copyToken">
        <font-awesome-icon icon="key" /> Copy token
      </button>
      <router-link class="dropdown-item" :to="{name: 'change-password'}">
        <font-awesome-icon icon="wrench" /> Change password
      </router-link>
      <div class="dropdown-divider"></div>
      <button class="dropdown-item" @click.prevent="signOut">
        <font-awesome-icon icon="sign-out-alt" /> Sign-out
      </button>
    </div>
  </span>
  <router-link v-else class="btn btn-sm btn-light" :to="{ name: 'sign-in' }">
    <font-awesome-icon icon="sign-in-alt" size="sm" /> Sign-in
  </router-link>
</template2>

<template>
  <b-dropdown v-if="$store.getters.isLoggedIn" variant="light" size="sm" right>

    <template v-slot:button-content>
      <font-awesome-icon icon="user-circle" size="sm" /> {{ $store.getters.username }}
    </template>

    <b-dropdown-item @click.prevent="copyToken">
        <font-awesome-icon icon="key" /> Copy token
    </b-dropdown-item>

    <b-dropdown-item :to="{name: 'change-password'}">
        <font-awesome-icon icon="wrench" /> Change password
    </b-dropdown-item>

    <b-dropdown-divider></b-dropdown-divider>

    <b-dropdown-item @click.prevent="signOut">
      <font-awesome-icon icon="sign-out-alt" /> Sign-out
    </b-dropdown-item>

  </b-dropdown>

  <router-link v-else class="btn btn-sm btn-light" :to="{ name: 'sign-in' }">
    <font-awesome-icon icon="sign-in-alt" size="sm" /> Sign-in
  </router-link>
</template>


<script type="text/javascript">
  import Constants from '../constants.js'

  export default {
    name: 'UserButton',
    methods: {
      copyToken() {
        let parent = this;
        this.$copyText(this.$store.getters.access_token).then(function () {
            parent.$root.$emit('feedback-message', 'info', "Token copied to Clipboard!");
          }, function () {
            parent.$root.$emit('feedback-message',
                         'warning',
                         "Unable to copy token to clipboard 😞<br />" +
                         "Copy it manually:<br /><input type=\"text\" value=\"" + parent.$store.getters.access_token + "\" />");
          });
      },
      signOut() {
        let parent = this;
        let msg = "";
        if (Constants.now().isAfter(this.$store.getters.token_expiry)) {
          msg = "Your token already expired anyway 🤷🏾‍♂️";
        } else {
          let human_diff = Constants.format_duration(this.$store.getters.token_expiry.diff());
          msg = "Your token is still valid for about " + human_diff + " though";
        }
        parent.$store.dispatch('clearAuthentication');
        parent.$cookie.delete('token_data');
        parent.$root.$emit('feedback-message', 'info', "<strong>Signed-out!</strong><br />" + msg);
      }
    },
  }
</script>

<style type="text/css" scoped>
  .dropdown-menu {
      font-size: .9rem;
      padding: .2rem 0;
      outline: none;
  }

  .dropdown-item {
      padding: .25rem .5rem;
  }
</style>
