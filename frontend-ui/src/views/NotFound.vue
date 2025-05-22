<!-- Friendly fallback for unmatched routes -->

<template>
  <div class="container">
    <h1> Not Found <font-awesome-icon icon="carrot" /></h1>
    <p>Sorry, this content was not found. Maybe you'd like to <BackButton /></p>
  </div>
</template>

<script>
  import BackButton from '../components/BackButton.vue'

  export default {
    name: 'NotFound',
    components: {BackButton},
  }
</script>
