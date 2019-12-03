<!-- Sign-in button that transforms into a user menu
  - send to sign-in if not logged-in
  - copy token to clipboard
  - send to change-password (TBI)
  - log-out -->

<template>
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
      <router-link class="dropdown-item" :to="{name: 'sign-in'}">
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
</template>


<script type="text/javascript">
  import Constants from '../constants.js'

  export default {
    name: 'UserButton',
    methods: {
      copyToken: function () {
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
      signOut: function() {
        let parent = this;
        let msg = "";
        if (Constants.now().isAfter(this.$store.getters.token_expiry)) {
          msg = "Your token already expired anyway 🤷🏾‍♂️";
        } else {
          let minutes = (this.$store.getters.token_expiry.diff() / 1000 / 60).toFixed();
          msg = "Your token is still valid for " + minutes + " minutes though";
        }
        parent.$store.dispatch('clearAuthentication');
        parent.$root.$emit('feedback-message', 'info', "<strong>Signed-out!</strong><br />" + msg);
      }
    },
  }
</script>
