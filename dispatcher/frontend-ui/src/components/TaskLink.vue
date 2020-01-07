<template>
  <router-link v-if="tooltip" v-tooltip="format_dt(updated_at)" :to="to">{{ text }}
  </router-link>
  <router-link v-else :to="to">{{ text }}
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
      }
    },
    computed: {
      to() {
        return {name: 'task-detail', params: {_id: this._id}};
      },
      text() {
        return this.from_now(this.updated_at);
      }
    }
  }
</script>

