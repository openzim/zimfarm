<!-- Floating bootstrap-alert feedback text for non-located actions -->

<template>
  <div class="container">
    <div class="col-xs-12 col-sm-8 col-md-6 col-lg-5 alertbox alert" :class="alertClass" role="alert" v-if="message">
      <font-awesome-icon class="dismiss" icon="times" size="sm" @click="dismiss" />
      <div v-html="message"></div>
    </div>
  </div>
</template>

<script type="text/javascript">
  export default {
    name: 'AlertFeedback',
    data() {
      return {
        level: null,  // bootstrap-alert-like class to use: info, success, warning, danger
        message: null,  // message to display
      };
    },
    computed: { // actual bootstrap class from level
      alertClass() { return 'alert-' + this.level; }
    },
    methods: {
      dismiss() { // remove alert
        this.level = this.message = null;
      },
    },
    beforeMount(){
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

  .container {
    position: relative;
  }
  .alertbox {
    margin-left:auto;
    margin-right: 0;

    position: fixed;
    z-index: 900;

    width: auto;
    right: .75rem;
    box-sizing: border-box;
    padding: .8rem;
  }
  @media (max-width: 575.98px) {
    .alertbox {
      border-radius: 0;
      right: 0;
      width: 100%;
    }
  }
</style>
