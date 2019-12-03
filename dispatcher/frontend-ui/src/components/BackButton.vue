<!-- Simple back buttton to mimick browser back -->
<template>
  <button class="btn btn-secondary btn-sm" @click.prevent="goBack"><font-awesome-icon icon="arrow-circle-left" size="sm" /> Go Back</button>
</template>

<script type="text/javascript">
  export default {
    name: 'BackButton',
    methods: {
      goBack: function() {
        this.$router.go(-1);
      }
    }
  }
</script>
