<template>
  <div class="alert alert-danger">
    <p><font-awesome-icon icon="exclamation-triangle" /> You are about to <strong>permanently delete</strong> user account <code>{{ username }}</code>.</p>
    <b-form inline @submit.prevent="deleteUser">
      <p>Please type its <em>username</em> to confirm:
        <b-input autofocus class="mr-2" size="sm" v-model="form_username" placeholder="Type username here" />
        <b-button type="submit" :disabled="!ready" variant="danger" size="sm">delete user</b-button>
      </p>
    </b-form>
  </div>
</template>

<script type="text/javascript">
  import Constants from '../constants.js'
  import ZimfarmMixins from '../components/Mixins.js'

  export default {
    name: 'DeleteUser',
    mixins: [ZimfarmMixins],
    props: {
      username: String
    },
    data() {
      return {
        form_username: null,
      };
    },
    computed: {
      ready() { return this.username && this.form_username && this.username == this.form_username; },
    },
    methods: {
      deleteUser() {
        if (!this.ready)
          return;

        let parent = this;
        parent.toggleLoader("deleting user…");
        parent.$root.axios.delete('/users/' + parent.username)
          .then(function () {
            parent.alertSuccess("Deleted!", "User account <code>"+ parent.username +"</code> has been removed.");
            parent.redirectTo('users-list');
          })
          .catch(function (error) {
            parent.alertDanger("Error", Constants.standardHTTPError(error.response));
          })
          .then(function () {
            parent.toggleLoader(false);
          });
      },
    },
  }
</script>
