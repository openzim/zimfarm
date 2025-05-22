<template>
  <router-link v-if="tooltip" v-tooltip="format_dt(updated_at)" :to="to">{{ display_text }}</router-link>
  <router-link v-else :to="to">{{ display_text }}
  </router-link>
</template>

<script type="text/javascript">
  import ZimfarmMixins from '../components/Mixins.js'

  export default {
    name: 'TaskLink',
    mixins: [ZimfarmMixins],
    props: {
      _id: String,
      updated_at: String,
      tooltip: {
        type: Boolean,
        default: true,
      },
      text: {
        type: String,
        default: null,
      }
    },
    computed: {
      to() {
        return {name: 'task-detail', params: {_id: this._id}};
      },
      display_text() {
        return this.text === null ? this.from_now(this.updated_at) : this.text;
      }
    }
  }
</script>

