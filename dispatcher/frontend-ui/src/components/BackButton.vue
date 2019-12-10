<!-- Simple back buttton to mimick browser back -->
<template>
  <button class="btn btn-secondary btn-sm" @click.prevent="goBack" v-show="has_history">
    <font-awesome-icon icon="arrow-circle-left" size="sm" /> Go Back
  </button>
</template>

<script type="text/javascript">
  export default {
    name: 'BackButton',
    computed: {
      has_history() { return window.history.length > 1; }
    },
    methods: {
      goBack() {
        this.$router.back();
      }
    }
  }
</script>
