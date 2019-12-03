<!-- Full-featured button to start a schedule by its name

  - disabled if not signed-in
  - displays a spinner on click
  - calls the API in the background
  - displays result as an AlertFeedback -->

<template>
  <button class="btn btn-sm btn-primary" @click.prevent="fire" :disabled="!$store.getters.username">
    <font-awesome-icon icon="spinner" size="sm" spin v-show="should_display_loader" /> {{ button_text }}
  </button>
</template>

<script type="text/javascript">
  import Constants from '../constants.js'

  export default {
    name: 'FireScheduleButton',
    props: {
      name: String
    },
    computed: {
      should_display_loader: function() {
        return this.working;
      },
      button_text: function() {
        if (this.working) {
          return "requesting task…";
        } else {
          return "🔥 fire " + this.name;
        }
      },
    },
    methods: {
      fire: function() {
        let parent = this;

        parent.working = true;
        parent.$root.axios.post('/requested-tasks/', {schedule_names: [parent.name]})
        .then(function (response) {
            let req_id;
            try {
               req_id = response.data.requested[0];
            } catch { console.error("no id?"); }
            let msg = "Schedule <em>" + parent.name + "</em> has been requested as <code>" + req_id + "</code>.";
            parent.$root.$emit('feedback-message', 'success', "<strong>Scheduled!</strong><br />" + msg);
          })
          .catch(function (error) {
            parent.$root.$emit('feedback-message',
                               'danger',
                               "<strong>Not Scheduled!</strong><br />" + Constants.standardHTTPError(error.response));
          })
          .then(function () {
            parent.working = false;
          });
      }
    }
  }
</script>
