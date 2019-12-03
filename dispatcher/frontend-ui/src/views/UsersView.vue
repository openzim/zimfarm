<!-- Users management view:
  - list of users
  - user profile (TBI) -->

<template>
  <div class="container">
    <table v-if="!error" class="table table-responsive-sm table-striped table-hover">
      <thead class="thead-dark">
        <tr><th>Username</th><th>Email</th></tr>
      </thead>
      <tbody>
        <tr v-for="user in users" :key="user.username">
          <td><router-link :to="{name: 'user-detail', params: {'username': user.username}}">{{ user.username }}</router-link></td>
          <td>{{ user.email }}</td>
        </tr>
      </tbody>
    </table>
    <ErrorMessage :message="error" v-else />
  </div>
</template>

<script type="text/javascript">
  import Constants from '../constants.js'
  import ZimfarmMixins from '../components/Mixins.js'
  import ErrorMessage from '../components/ErrorMessage.vue'

  export default {
    name: 'UsersView',
    mixins: [ZimfarmMixins],
    components: {ErrorMessage},
    data: function () {
      return {
        error: null,  // API generated error message
        users: [],  // list of users returned by API
      };
    },
    methods: {
      loadUsersList: function() {  // load users list from API
        let parent = this;

        parent.toggleLoader("fetching workers…");
        parent.$root.axios.get('/users/')
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
    mounted: function() {
      this.loadUsersList();
    },
  }
</script>
