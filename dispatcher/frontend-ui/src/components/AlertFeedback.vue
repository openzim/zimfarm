<!-- Floating bootstrap-alert feedback text for non-located actions -->

<template>
  <div class="container">
    <b-alert v-if="message"
             :show="dismissCountDown"
             dismissible
             fade
             :variant="level"
             @dismiss-count-down="countDownChanged">
      <div v-html="message"></div>
    </b-alert>
  </div>
</template>

<script type="text/javascript">
  import Constants from '../constants.js'

  export default {
    name: 'AlertFeedback',
    data() {
      return {
        level: null,  // bootstrap-alert-like class to use: info, success, warning, danger
        message: null,  // message to display
        auto_dismiss: true,  // whether to automatically hide or not
        dismissCountDown: 0,  // live-updating counter
      };
    },
    methods: {
      countDownChanged(dismissCountDown) {
        if (!this.auto_dismiss)
          return;

        this.dismissCountDown = dismissCountDown;
      },
    },
    beforeMount(){
      let parent = this;
      this.$root.$on('feedback-message', function (level, message, duration) {
        parent.level = level;
        parent.message = message;
        // if dismissCountDown is not a number, it won't trigger countDownChanged
        if (duration === undefined)
            duration = Constants.ALERT_DEFAULT_DURATION;
        if (duration === true)
            duration = Constants.ALERT_PERMANENT_DURATION;

        // parent.dismissCountDown = duration;
        // parent.auto_dismiss = (duration === true) ? false : true;

        // using only permenent alerts for now
        parent.dismissCountDown = Constants.ALERT_PERMANENT_DURATION;
        parent.auto_dismiss = false;
      });
    }
  }
</script>

