<!-- Pipeline View showing a list of tasks -->

<template>
  <div class="container">
    <TasksList :filter="filter" />
  </div>
</template>

<script>
  import TasksList from '../components/TasksList.vue'

  export default {
    name: 'PipelineView',
    props: {
      filter: {
        type: String,
        default: "todo"
      },
    },
    components: {TasksList},
  }
</script>
