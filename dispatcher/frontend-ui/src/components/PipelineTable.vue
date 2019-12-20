<!-- Generic table listing tasks in a pipeline

  - supports todo, doing, done, failed -->

<template>
  <div>
    <table class="table table-responsive-sm table-striped" v-if="!error">
      <caption>Showing max. <select v-model="selectedLimit" @change.prevent="limitChanged">
          <option v-for="limit in limits" :key="limit" :value="limit">{{ limit }}</option>
        </select> out of <strong>{{ total_results }} results</strong>
      </caption>
      <thead v-if="selectedTable == 'todo'">
        <tr>
          <th>Schedule</th>
          <th>Requested</th>
          <th>By</th>
          <th>Resources</th>
          <th>Worker</th>
          <th v-show="canUnRequestTasks">Remove</th>
        </tr>
      </thead>
      <thead v-if="selectedTable == 'doing'">
        <tr><th>Schedule</th><th>Started</th><th>Worker</th></tr>
      </thead>
      <thead v-if="selectedTable == 'done'">
        <tr><th>Schedule</th><th>Completed</th><th>Worker</th><th>Duration</th></tr>
      </thead>
      <thead v-if="selectedTable == 'failed'">
        <tr><th>Schedule</th><th>Stopped</th><th>Worker</th><th>Duration</th><th>Status</th></tr>
      </thead>
      <tbody>
        <tr v-for="task in tasks" :key="task._id">
          <td v-if="selectedTable != 'todo'">
            <router-link :to="{name: 'task-detail', params: {_id: task._id}}">{{ task.schedule_name }}</router-link>
          </td>
          <td v-else>
            <router-link :to="{name: 'schedule-detail', params: {schedule_name: task.schedule_name}}">{{ task.schedule_name }}</router-link>
            <span class="text-warning" v-if="task.priority > 0">&nbsp;<font-awesome-icon size="sm" icon="fire" /></span>
          </td>
          <td v-if="selectedTable == 'todo'"
              v-tooltip="{content: format_dt(task.timestamp.requested), delay: 10}">{{ task.timestamp.requested | from_now }}</td>
          <td v-if="selectedTable == 'todo'">{{ task.requested_by }}</td>
          <td v-if="selectedTable == 'todo'"><ResourceBadge kind="cpu" :value="task.config.resources.cpu" />
              <ResourceBadge kind="memory" :value="task.config.resources.memory" />
              <ResourceBadge kind="disk" :value="task.config.resources.disk" /></td>
          <td v-if="selectedTable == 'doing'"
              v-tooltip="{content: format_dt(task.timestamp.reserved), delay: 10}">{{ task.timestamp.reserved | from_now }}</td>
          <td v-if="selectedTable == 'done'"
              v-tooltip="{content: format_dt(task.timestamp.succeeded), delay: 10}">{{ task.timestamp.succeeded | from_now }}</td>
          <td v-if="selectedTable == 'failed'"
              v-tooltip="{content: format_dt(task.timestamp.failed), delay: 10}">{{ task.timestamp.failed | from_now }}</td>
          <td>{{ task.worker || 'n/a' }}</td>
          <td v-if="selectedTable == 'done' || selectedTable == 'failed'">{{ task.duration }}</td>
          <td v-if="selectedTable == 'failed'">{{ task.status }}</td>
          <td v-if="selectedTable == 'todo'" v-show="canUnRequestTasks"><RemoveRequestedTaskButton :_id="task._id" @requestedtasksremoved="loadData" /></td>
        </tr>
      </tbody>
    </table>
    <ErrorMessage :message="error" v-else />
  </div>
</template>

<script type="text/javascript">
  import Constants from '../constants.js'
  import ZimfarmMixins from '../components/Mixins.js'
  import ErrorMessage from '../components/ErrorMessage.vue'
  import RemoveRequestedTaskButton from '../components/RemoveRequestedTaskButton.vue'
  import ResourceBadge from '../components/ResourceBadge.vue'

  export default {
    name: 'PipelineTable',
    mixins: [ZimfarmMixins],
    components: {ErrorMessage, RemoveRequestedTaskButton, ResourceBadge},
    props: {
      selectedTable: String, // applied filter: todo, doing, done, failed
    },
    data() {
      return {
        tasks: [], // list of tasks returned by API
        meta: {}, // API query metadata (count, skip, limit)
        error: false, // error string to display on API error
        timer: null,  // auto-refresh timer
      };
    },
    computed: {
      total_results() { // total (non-paginated) tasks for query from API
        return (this.meta && this.meta.count) ? this.meta.count : 0;
      }
    },
    methods: {
      limitChanged() {
        this.saveLimitPreference(this.selectedLimit);
        this.loadData();
      },
      resetData() { // reset data holders
        this.error = null;
        this.tasks = [];
        this.meta = {};
      },
      loadGenericData(url, params, item_transform) {
        let parent = this;
        parent.toggleLoader("fetching tasks…");

        parent.$root.axios.get(url, {params})
          .then(function (response) {
              parent.resetData();
              parent.meta = response.data.meta;
              parent.tasks = response.data.items.map(item_transform);
          })
          .catch(function (error) {
            parent.error = Constants.standardHTTPError(error.response);
          })
          .then(function () {
              parent.toggleLoader(false);
          });
      },
      loadData() {
        if (this.selectedTable == 'todo') {
          this.loadGenericData('/requested-tasks/',
                               {limit: this.selectedLimit},
                               function (item) { return item; });
        }
        if (this.selectedTable == 'doing') {
          this.loadGenericData('/tasks/',
                               {limit: this.selectedLimit,
                                status: ["reserved", "started", "scraper_started", "cancel_requested"]},
                               function (item) { return item; });
        }
        if (this.selectedTable == 'done') {
          this.loadGenericData('/tasks/',
                               {limit: this.selectedLimit,
                                status: ["succeeded"]},
                               function (item) {
                                item["duration"] = Constants.format_duration_between(item.timestamp.started, item["timestamp"]["succeeded"]);
                                return item;
                               });
        }
        if (this.selectedTable == 'failed') {
          this.loadGenericData('/tasks/',
                               {limit: this.selectedLimit,
                                status: ["scraper_killed", "failed", "canceled"]},
                               function (item) {
                                // TODO: make safer
                                let event_ts = item.timestamp.canceled ? item.timestamp.canceled : item.timestamp.failed;
                                item["duration"] = Constants.format_duration_between(item.timestamp.started, event_ts);
                                return item;
                               });
        }
      },
    },
    mounted() {
      this.loadData();
      this.timer = setInterval(this.loadData, 60000);
    },
    beforeDestroy () {
      clearInterval(this.timer)
    },
    watch: {
      selectedTable() {
        this.loadData();
      },
    }
  };
</script>
