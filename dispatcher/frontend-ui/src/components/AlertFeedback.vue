<!-- Floating bootstrap-alert feedback text for non-located actions -->

<template>
  <div class="alertbox alert" :class="alertClass" role="alert" v-if="message">
    <font-awesome-icon class="dismiss" icon="times" size="sm" @click="dismiss" />
    <div v-html="message"></div>
  </div>
</template>

<script type="text/javascript">
  export default {
    name: 'AlertFeedback',
    data: function () {
      return {
        level: null,  // bootstrap-alert-like class to use: info, success, warning, danger
        message: null  /// message to display
      };
    },
    computed: { // actual bootstrap class from level
      alertClass: function() { return 'alert-' + this.level; }
    },
    methods: {
      dismiss: function() { // remove alert
        this.level = this.message = null;
      },
    },
    beforeMount: function(){
      let parent = this;
      this.$root.$on('feedback-message', function (level, message) {
        parent.level = level;
        parent.message = message;
      });
    }
  }
</script>

<style type="text/css" scoped>
  .dismiss {
    position: absolute;
    top: .25rem;
    right: .25rem;
  }
  .dismiss:hover {
    cursor: pointer;
    color: #333333;
  }
  .alertbox {
    float: right;
    margin-right: 1rem;
    max-width: 40rem;
  }
</style>
