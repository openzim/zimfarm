<!-- Filterable list of schedules with filtered-fire button -->

<template>
  <SchedulesList></SchedulesList>
</template>

<script type="text/javascript">
  import SchedulesList from '../components/SchedulesList.vue'

  export default {
    name: 'SchedulesView',
    components: {SchedulesList},
  };
</script>
