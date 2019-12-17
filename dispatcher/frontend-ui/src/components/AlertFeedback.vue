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
  export default {
    name: 'AlertFeedback',
    data() {
      return {
        level: null,  // bootstrap-alert-like class to use: info, success, warning, danger
        message: null,  // message to display
        dismissCountDown: 0,  // live-updating counter
      };
    },
    methods: {
      countDownChanged(dismissCountDown) { this.dismissCountDown = dismissCountDown; },
    },
    beforeMount(){
      let parent = this;
      this.$root.$on('feedback-message', function (level, message) {
        parent.level = level;
        parent.message = message;
        parent.dismissCountDown = 5;
      });
    }
  }
</script>

