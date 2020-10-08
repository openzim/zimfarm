<template>
  <table class="table table-sm table-striped" :class="{'table-responsive': shrink}">
    <tbody>
      <tr v-for="(value, name) in flags" :key="name">
        <td><code>{{ name }}</code></td>
        <td v-if="is_protected_key(name)" v-tooltip="'Actual content hidden'">{{ secret_replacement }}</td>
        <td v-else>{{ value }}</td>
      </tr>
    </tbody>
  </table>
</template>

<script type="text/javascript">
  import Constants from '../constants.js'

  export default {
    name: 'FlagsList',
    props: {
      flags: Object,
      shrink: {
        type: Boolean,
        default: false
      },
      secret_fields: Array,
    },
    computed: {
      secret_replacement() { return Constants.secret_replacement; }
    },
    methods: {
      is_protected_key(key) { return this.secret_fields ? this.secret_fields.indexOf(key) != -1: false; },
    },
  }
</script>
