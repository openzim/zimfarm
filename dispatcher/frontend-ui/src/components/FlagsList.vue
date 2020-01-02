<template>
  <table class="table table-sm table-striped" :class="{'table-responsive': shrink}">
    <tbody>
      <tr v-for="(value, name) in flags" :key="name">
        <td><code>{{ name }}</code></td><td>{{ value }}</td>
      </tr>
    </tbody>
  </table>
</template>

<script type="text/javascript">
  export default {
    name: 'FlagsList',
    props: {
      flags: Object,
      shrink: {
        type: Boolean,
        default: false
      }
    },
  }
</script>
