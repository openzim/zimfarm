<template>
  <div>
    <b-form inline @submit.prevent="updateUser">

      <label class="mr-2" for="cu_email">Role</label>
      <b-select class="mr-2" v-model="form.role">
        <option v-for="role in roles" :key="role" :value="role">{{ role }}</option>
      </b-select>

      <label class="sr-only" for="cu_email">Email</label>
      <b-input class="mr-2" type="email" id="cu_email" placeholder="Email" v-model="form.email"></b-input>

      <b-button type="submit" class="form-control" :disabled="!payload" variant="primary">Update User</b-button>
    </b-form>

    <hr />

    <b-form inline @submit.prevent="changePassword">
      <label class="mr-2" for="cu_password">Password (generated)</label>
      <b-input class="mr-2" id="cu_password" placeholder="Password" required v-model="form.password"></b-input>
      <b-button type="submit" class="form-control" :disabled="!form.password" variant="primary">Change Password</b-button>
    </b-form>

    <hr />

    <b-form v-if="form.role == 'worker'" inline @submit.prevent="addKey">
      <label class="mr-2" for="key_file">RSA Public Key</label>
      <input id="key_file" type="file" ref="keyFile" @change="keyFileSelected" />
      <b-button type="submit" class="form-control" variant="primary" :disabled="Object.isEmpty(key_payload)">Add SSH Key</b-button>
    </b-form>
  </div>
</template>

<script type="text/javascript">
  import passwordGen from 'password-generator'

  import Constants from '../constants.js'
  import ZimfarmMixins from '../components/Mixins.js'

  export default {
    name: 'UpdateUser',
    mixins: [ZimfarmMixins],
    props: {
      user: Object
    },
    data() {
      return {
        form: {},
        keyForm: {name: "", key: ""}
      };
    },
    computed: {
      payload() {
        let payload = {role: this.form.role};
        if (this.form.email != this.user.email)
          payload.email = this.form.email;
        return payload;
      },
      key_payload() {
        const payload = {name: this.keyForm.name, key: this.keyForm.key};
        if (!payload.name.length || !payload.key.length)
          return {};
        return payload;
      },
      roles() { return Constants.ROLES; },
      ready() { return false; },
    },
    methods: {
      keyFileSelected() {
        let parent = this;
        parent.keyForm.key = parent.keyForm.name = "";

        if (!this.$refs.keyFile.files || !this.$refs.keyFile.files.length){
          parent.alertDanger("Error selecting file. Please try again.");
          return;
        }

        let file = this.$refs.keyFile.files[0];
        if (file.size > 512) {
          parent.alertDanger("Error", "File {0} doesn't appear to be an RSA public file (too large).".format(file.name));
          return;
        }

        let reader = new FileReader();
        reader.onerror = evt => {
          parent.alertDanger("Error", "File {0} failed to read: {1).".format(file.name, evt));
        }
        reader.onload = evt => {
          let parts = evt.target.result.trim().split(/\s/);
          if (parts.length != 3) {
            parent.alertDanger("Error", "File {0} doesn't appear to be an RSA public file (format).".format(file.name));
            return;
          }

          if (parts[0].toLowerCase().indexOf("rsa") == -1) {
            parent.alertDanger("Error", "File {0} doesn't appear to be an RSA public file (no RSA prefix).".format(file.name));
            return;
          }
          parent.keyForm.key = parts[1].trim();
          parent.keyForm.name = parts[2].trim();
        }
        reader.readAsText(file, "UTF-8");
      },
      genPassword() { return passwordGen(8, true); },
      changePassword() {
        let parent = this;
        if (!parent.form.password)
          return;

        parent.toggleLoader("changing password…");
        parent.queryAPI('patch', '/users/' + parent.user.username + '/password', {new: parent.form.password})
        .then(function () {
            parent.alertSuccess(
              "Password Changed!",
              "Password for <code>" + parent.user.username + "</code> has been changed to <code>" + parent.form.password + "</code>.",
              true
            );
            parent.redirectTo('users-list');
        })
        .catch(function (error) {
          parent.alertDanger("Error", Constants.standardHTTPError(error.response), 10);
        })
        .then(function () {
            parent.toggleLoader(false);
            parent.scrollToTop();
        });
      },
      updateUser() {
        if (!this.payload)
          return;

        let parent = this;
        parent.toggleLoader("updating user…");
        parent.queryAPI('patch', '/users/' + parent.user.username, this.payload)
          .then(function () {
            parent.alertSuccess("Updated!", "User account <code>"+ parent.user.username +"</code> has been updated.");
            parent.redirectTo('users-list');
          })
          .catch(function (error) {
            parent.alertDanger("Error", Constants.standardHTTPError(error.response), 10);
          })
          .then(function () {
            parent.toggleLoader(false);
          });
      },
      addKey() { // request token on API using credentials
        if (!this.key_payload)
          return;
        let parent = this;
        parent.toggleLoader("adding SSH key…");
        parent.queryAPI('post', '/users/' + parent.user.username + '/keys', this.key_payload)
            .then(function () {
              parent.alertSuccess("Added!", "SSH key has been added.");
              parent.redirectTo('users-list');
            })
            .catch(function (error) {
              parent.alertDanger("Error", Constants.standardHTTPError(error.response), 10);
            })
            .then(function () {
              parent.toggleLoader(false);
            });
        },
    },
    mounted() {
      if (!this.form.length && this.user) {
        let role = Constants.ROLES.indexOf(this.user.role) == -1 ? "editor" : this.user.role;
        this.form = {
          email: this.user.email,
          role: role,
          password: this.genPassword(),
        }
      }
    },
  }
</script>
