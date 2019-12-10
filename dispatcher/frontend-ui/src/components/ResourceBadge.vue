<template>
  <span class="badge badge-light mr-2">
    <font-awesome-icon :icon="icon" /> {{ displayed_value }}
  </span>
</template>

<script type="text/javascript">
  import filesize from 'filesize';

  export default {
    name: 'ResourceBadge',
    props: {
      kind: String,  // cpu, memory, disk
      value: Number, // actual data
      human_value: String,  // human repr of value (instead of raw one)
    },
    computed: {
      displayed_value() {
        if (this.human_value)
          return this.human_value;
        return (this.kind == 'cpu') ? this.value : filesize(this.value); },
      icon() { return {cpu: 'microchip', memory: 'memory', disk: 'hdd'}[this.kind]; },
      tooltip_text() {
        if (!this.tooltip)
          return "-";
        return {cpu: "CPU", memory: "Memory", disk: "Disk"}[this.kind];
      },
    }
  }
</script>
