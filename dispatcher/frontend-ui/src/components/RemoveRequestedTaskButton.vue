<!-- Full-featured button to remove a requested task by its _id

  - disabled if not signed-in
  - displays a spinner on click
  - calls the API in the background
  - displays result as an AlertFeedback -->

<template>
  <button class="btn btn-sm btn-dark action-button"
          @click.prevent="removeTask"
          :disabled="!$store.getters.isLoggedIn"
          v-if="$store.getters.isLoggedIn">
    <span v-show="!should_display_loader">
      <font-awesome-icon icon="times" size="sm" /> remove
    </span>
    <span v-show="should_display_loader">
      <font-awesome-icon icon="spinner" size="sm" spin v-show="should_display_loader" /> Removing requested task…
    </span>
  </button>
</template>

<script type="text/javascript">
  import Constants from '../constants.js'

  export default {
    name: 'RemoveRequestedTaskButton',
    props: {
      _id: String
    },
    computed: {
      short_id() { return Constants.short_id(this._id); },
      should_display_loader() { return this.working; },
    },
    methods: {
      removeTask() {
        let parent = this;

        parent.working = true;
        parent.$root.axios.delete('/requested-tasks/' + parent._id)
          .then(function () {
            let msg = "Requested Task <code>" + Constants.short_id(parent._id) + "</code> has been removed.";

            parent.$root.$emit('feedback-message', 'success', "<strong>Un-scheduled!</strong><br />" + msg);
          })
          .catch(function (error) {
            parent.$root.$emit('feedback-message',
                               'danger',
                               "<strong>Not Un-scheduled!</strong><br />" + Constants.standardHTTPError(error.response));
          })
          .then(function () {
            parent.working = false;
            parent.$emit('requestedtasksremoved', parent._id);
          });
      }
    }
  }
</script>
