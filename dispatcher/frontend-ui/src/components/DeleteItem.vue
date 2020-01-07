<template>
  <div class="alert alert-danger">
    <p><font-awesome-icon icon="exclamation-triangle" /> You are about to <strong>permanently delete</strong> {{ description }} <code>{{ name }}</code>.</p>
    <b-form inline @submit.prevent="deleteItem">
      <p>Please type its <em>{{ property }}</em> to confirm:
        <b-input autofocus class="mr-2" size="sm" v-model="form_name" :placeholder="'Type ' + property + ' here'" />
        <b-button type="submit" :disabled="!ready" variant="danger" size="sm">delete {{ description }}</b-button>
      </p>
    </b-form>
  </div>
</template>

<script type="text/javascript">
  import Constants from '../constants.js'
  import ZimfarmMixins from '../components/Mixins.js'

  export default {
    name: 'DeleteItem',
    mixins: [ZimfarmMixins],
    props: {
      kind: String,
      name: String
    },
    data() {
      return {
        valid_kinds: ["user", "schedule"],
        form_name: null,
      };
    },
    computed: {
      is_valid() { return this.valid_kinds.indexOf(this.kind) != -1; },
      ready() { return this.name && this.form_name && this.name == this.form_name; },
      property() { return {user: "username", schedule: "name"}[this.kind] },
      description() { return {user: "user account", schedule: "recipe"}[this.kind] },
      target() { return {user: "users-list", schedule: "schedules-list"}[this.kind]; },
      url() { return {user: "/users/" + this.name, schedule: "/schedules/" + this.name}[this.kind]; },
    },
    methods: {
      deleteItem() {
        let parent = this;
        parent.toggleLoader("deleting " + parent.description + "…");
        parent.queryAPI('delete', parent.url)
          .then(function () {
            parent.alertSuccess("Deleted!", parent.description + " <code>"+ parent.name +"</code> has been removed.");
            parent.redirectTo(parent.target);
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
