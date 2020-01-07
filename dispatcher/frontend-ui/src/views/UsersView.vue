<!-- Users management view:
  - list of users
  - user profile (TBI) -->

<template>
  <div class="container" v-show="canReadUsers">

    <div v-show="canCreateUsers">
      <b-form class="row" @submit.prevent="createUser">
        <div class="col-sm-12 col-md-6 col-lg-3 mb-1">
          <label class="sr-only" for="cu_username">Username</label>
          <b-input id="cu_username" placeholder="Username" v-model="form.username"></b-input>
        </div>

        <div class="col-sm-12 col-md-6 col-lg-3 mb-1">
          <label class="sr-only" for="cu_email">Email</label>
          <b-input type="email" id="cu_email" placeholder="Email" v-model="form.email"></b-input>
        </div>

        <div class="col-sm-12 col-md-6 col-lg-3 mb-1">
          <b-select v-model="form.role">
            <option v-for="role in roles" :key="role" :value="role">{{ role }}</option>
          </b-select>
        </div>
        <div class="col-sm-12 col-md-6 col-lg-3 mb-1">
          <b-button type="submit" class="form-control" :disabled="!payload" variant="primary">Create User</b-button>
        </div>
      </b-form>
    </div>

    <hr />

    <table v-if="!error" class="table table-striped table-hover">
      <tbody>
        <tr v-for="user in users" :key="user.username">
          <td><router-link :to="{name: 'user-detail', params: {'username': user.username}}">{{ user.username }}</router-link></td>
          <td>{{ user.role }}</td>
          <td><a :href="'mailto:' + user.email">{{ user.email }}</a></td>
        </tr>
      </tbody>
    </table>

    <ErrorMessage :message="error" v-if="error" />
  </div>
</template>

<script type="text/javascript">
  import passwordGen from 'password-generator'
  import Constants from '../constants.js'
  import ZimfarmMixins from '../components/Mixins.js'
  import ErrorMessage from '../components/ErrorMessage.vue'

  export default {
    name: 'UsersView',
    mixins: [ZimfarmMixins],
    components: {ErrorMessage},
    data() {
      return {
        error: null,  // API generated error message
        users: [],  // list of users returned by API

        form: {role: "editor"},  // create user data holder
      };
    },
    computed: {
      roles() { return Constants.ROLES; },
      payload() {
        let payload = {role: this.form.role};
        if (this.form.username)
          payload.username = this.form.username;
        if (this.form.email)
          payload.email = this.form.email;

        if (Object.keys(payload).length == 1)
          return null;
        return payload;
      },
    },
    methods: {
      genPassword() { return passwordGen(8, true); },
      createUser() {
        if (this.payload === null) {
          return;
        }

        let payload = Constants.duplicate(this.payload);
        let parent = this;
        payload.password = this.genPassword();
        parent.toggleLoader("creating user…");
        parent.queryAPI('post', '/users/', payload)
        .then(function () {
            parent.alertSuccess(
              "User Created!",
              "User <code>" + payload.username + "</code> has been created with password <code>" + payload.password + "</code>.",
              false
            );
            parent.loadUsersList();
        })
        .catch(function (error) {
          parent.alertDanger("Error", Constants.standardHTTPError(error.response));
        })
        .then(function () {
            parent.toggleLoader(false);
            parent.scrollToTop();
        });
      },
      loadUsersList() {  // load users list from API
        let parent = this;

        parent.toggleLoader("fetching workers…");
        parent.queryAPI('get', '/users/')
          .then(function (response) {
            parent.error = null;
            parent.users = [];
            for (var i=0; i<response.data.items.length; i++){
              parent.users.push(response.data.items[i]);
            }
          })
          .catch(function (error) {
            parent.error = Constants.standardHTTPError(error.response);
          })
          .then(function () {
            parent.toggleLoader(false);
          });
      },
    },
    mounted() {
      if (!this.canReadUsers) {
        this.alertAccessRefused("users.read");
        this.redirectTo('home');
        return;
      }
      this.loadUsersList();
    },
  }
</script>
