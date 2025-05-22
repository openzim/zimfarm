<!-- Loading feedback to inform network operation is ongoing

  - displayed as a spinner on top of the carrot logo
  - displayed based on store's loadingstatus
  - hover displays an optionnal descriptive text -->

<template>
  <span v-if="should_display"
        id="main_loader"
        v-tooltip="loading_text">
        <font-awesome-icon icon="spinner" size="lg" spin />
  </span>
</template>

<script type="text/javascript">
  export default {
    name: 'Loading',
    computed: {
      should_display() {
        return this.$store.getters.loadingStatus.should_display;
      },
      loading_text() {
        return this.$store.getters.loadingStatus.text;
      }
    }
  }
</script>

<style type="text/css" scoped>
#main_loader {
  color: white;
  position: absolute;
  top: 0;
  left: 0;
  padding: 0.4rem;
}
</style>
