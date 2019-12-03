<!-- Filterable list of tasks based on pipeline -->

<template>
  <div>
    <ul class="nav nav-pills mb-2">
      <li class="nav-item">
        <router-link class="nav-link" :to="{ name: 'pipeline-filtered', params: {filter: 'todo' }}">TODO</router-link>
      </li>
      <li class="nav-item">
        <router-link class="nav-link" :to="{ name: 'pipeline-filtered', params: {filter: 'doing' }}">DOING</router-link>
      </li>
      <li class="nav-item">
        <router-link class="nav-link" :to="{ name: 'pipeline-filtered', params: {filter: 'done' }}">DONE</router-link>
      </li>
      <li class="nav-item">
        <router-link class="nav-link" :to="{ name: 'pipeline-filtered', params: {filter: 'failed' }}">FAILED</router-link>
      </li>
    </ul>
    <PipelineTable :selectedTable="filter" />
  </div>
</template>

<script type="text/javascript">
  import PipelineTable from './PipelineTable.vue'

  export default {
    name: 'TasksList',
    components: {PipelineTable},
    props: {
      filter: String,  // which filter to use
    }
  }
</script>
