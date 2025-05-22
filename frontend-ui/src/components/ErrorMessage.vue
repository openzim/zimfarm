<!-- Alert string to diplay an API-generated error message instead of expected content -->

<template>
  <p class="alert alert-danger" v-if="message">{{ message }}</p>
</template>

<script type="text/javascript">
  export default {
    name: 'ErrorMessage',
    props: {
      message: {
        type: String,
        default: null
      }
    }
  }
</script>
