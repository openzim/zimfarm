<!-- User management view:
  - Detail
  - change role
  - change password -->

<template>
  <div class="container">
    <h2><code>{{ username }}</code><span v-if="user"> (<code>{{ user.role }}</code>)</span></h2>

    <div v-if="!error && user">
      <ul class="nav nav-tabs">
        <li class="nav-item" :class="{ active: selectedTab == 'details'}">
          <router-link class="nav-link"
                       active-class="dummy"
                       :class="{ active: selectedTab == 'details'}"
                       :to="{name: 'user-detail', params: {username: username}}">
            Profile
          </router-link>
        </li>
        <li class="nav-item" :class="{ active: selectedTab == 'edit'}">
          <router-link class="nav-link"
                       active-class="dummy"
                       :class="{ active: selectedTab == 'edit'}"
                       :to="{name: 'user-detail-tab', params: {username: username, selectedTab: 'edit'}}">
            Edit
          </router-link>
        </li>
        <li v-show="canDeleteUser" class="nav-item" :class="{ active: selectedTab == 'delete'}">
          <router-link class="nav-link text-danger"
                       active-class="dummy"
                       :class="{ active: selectedTab == 'delete'}"
                       :to="{name: 'user-detail-tab', params: {username: username, selectedTab: 'delete'}}">
            Delete
          </router-link>
        </li>
      </ul>

      <div v-if="selectedTab == 'details'" class="tab-content">
        <p v-if="user.email"><a :href="'mailto:' + user.email">{{ user.email }}</a></p>

        <table class="table table-sm table-striped table-in-tab">
          <thead>
            <tr>
              <th>Permission</th>
              <th v-for="header in scope_main_headers" :key="header" class="text-center">{{ header }}</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="row in sorted_scope" :key="row.name">
              <th>{{ row.name }}</th>
              <td v-for="(perm, name) in row.perms" :key="name" class="text-center">
                <font-awesome-icon icon="check" v-if="perm" />
              </td>
            </tr>
          </tbody>
        </table>

        <table v-if="user.ssh_keys" class="table table-sm table-striped table-in-tab">
          <thead>
            <tr>
              <th>SSH Key</th>
              <th>Last Used</th>
              <th>Fingerprint</th>
              <th v-if="canSSHKeyUsers">Delete</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="ssh_key in user.ssh_keys" :key="ssh_key.name">
              <td>{{ ssh_key.name }}</td>
              <td v-tooltip="format_dt(ssh_key.last_used)">{{ ssh_key.last_used | from_now }}</td>
              <td ><code>{{ ssh_key.fingerprint }}</code></td>
              <td v-if="canSSHKeyUsers"><b-button variant="danger" size="sm" @click.prevent="confirmDelete(ssh_key)">Delete</b-button></td>
            </tr>
          </tbody>
        </table>
      </div>

      <div v-if="selectedTab == 'edit'" class="tab-content">
        <UpdateUser :user="user" v-if="user" />

      </div>

      <div v-if="selectedTab == 'delete'" class="tab-content">
        <DeleteItem kind="user" :name="username" />
      </div>
    </div>

    <ErrorMessage :message="error" v-if="error" />
  </div>
</template>

<script type="text/javascript">
  import Constants from '../constants.js'
  import ZimfarmMixins from '../components/Mixins.js'
  import ErrorMessage from '../components/ErrorMessage.vue'
  import DeleteItem from '../components/DeleteItem.vue'
  import UpdateUser from '../components/UpdateUser.vue'

  export default {
    name: 'UserView',
    mixins: [ZimfarmMixins],
    components: {ErrorMessage, DeleteItem, UpdateUser},
    props: {
      username: String,
      selectedTab: {  // currently selected tab: details, container, debug
        type: String,
        default: 'details'
      },
    },
    data() {
      return {
        error: null,  // API generated error message
        user: null,  // list of users returned by API
      };
    },
    computed: {
      scope() { return this.user.scope || {}},
      canDeleteUser() { return this.$root.has_perm("users", "delete"); },
      scope_main_headers() {
        return Object.keys(this.scope);
      },
      scope_secondary_headers() {
        let parent = this;
        let headers = [];
        this.scope_main_headers.forEach(function (namespace) {
          Object.keys(parent.scope[namespace]).forEach(function (perm_name) {
            if (headers.indexOf(perm_name) == -1)
              headers.push(perm_name);
          });
        });
        return headers;
      },
      sorted_scope() {
        let parent = this;
        let rows = [];
        parent.scope_secondary_headers.forEach(function (perm_name) {
          let row = {name: perm_name, perms: {}};
          parent.scope_main_headers.forEach(function (namespace) {
            row.perms[namespace] = parent.scope[namespace][perm_name] || false;
          });
          rows.push(row);
        });
        return rows;
      },
    },
    methods: {
      confirmDelete(ssh_key) {
        let parent = this;
        this.confirmAction("delete SSH Key “" + ssh_key.name + "”", function () {
          parent.deleteKey(ssh_key);
        });
      },
      deleteKey(ssh_key) {
        let parent = this;
        parent.toggleLoader("deleting key…");
        parent.queryAPI('delete', '/users/' + this.username + '/keys/' + ssh_key.fingerprint)
          .then(function () {
            parent.alertSuccess("Key Removed!", "SSH Key <code>" + ssh_key.name + "</code> has been removed.");
            parent.loadUser();
          })
          .catch(function (error) {
            parent.alertError(Constants.standardHTTPError(error.response));
          })
          .then(function () {
            parent.toggleLoader(false);
            parent.scrollToTop();
          });
      },
      loadUser() {  // load users list from API
        let parent = this;

        parent.toggleLoader("fetching user…");
        parent.queryAPI('get', '/users/' + this.username)
          .then(function (response) {
            parent.error = null;
            parent.user = response.data;
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
      this.loadUser();
    },
  }
</script>

<style type="text/css" scoped>
  .tab-content {
    padding: 1rem;
  }
</style>
