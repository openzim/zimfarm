<!-- Generic table listing tasks in a pipeline

  - supports todo, doing, done, failed -->

<template>
  <div>
    <table class="table table-responsive-md table-striped"
           v-if="!error"
           :class="{'loading': loading}">
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
        <tr><th>Schedule</th><th>Stopped</th><th>Worker</th><th>Duration</th><th>Status</th><th>Last Run</th></tr>
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
              v-tooltip="{content: format_dt(task.updated_at), delay: 10}">{{ task.updated_at | from_now }}</td>
          <td v-if="selectedTable == 'failed'"
              v-tooltip="{content: format_dt(task.updated_at), delay: 10}">{{ task.updated_at | from_now }}</td>
          <td><code v-if="task.worker">{{ task.worker }}</code><span v-else>n/a</span></td>
          <td v-if="selectedTable == 'done' || selectedTable == 'failed'">{{ task.duration }}</td>
          <td v-if="selectedTable == 'failed'"><code>{{ task.status }}</code></td>
          <td v-if="selectedTable == 'failed'">
            <span v-if="last_runs_loaded && schedules_last_runs[task.schedule_name]">
              <code :class="statusClass(getPropFor(task.schedule_name, 'status'))">
                {{ getPropFor(task.schedule_name, 'status') }}
              </code>,
              <TaskLink
                :_id="getPropFor(task.schedule_name, '_id', '-')"
                :updated_at="getPropFor(task.schedule_name, 'updated_at')" />
            </span>
          </td>
          <td v-if="selectedTable == 'todo'" v-show="canUnRequestTasks"><RemoveRequestedTaskButton :_id="task._id" @requestedtasksremoved="loadData" /></td>
        </tr>
      </tbody>
    </table>
    <ErrorMessage :message="error" v-else />
  </div>
</template>

<script type="text/javascript">
  import axios from 'axios'

  import Constants from '../constants.js'
  import ZimfarmMixins from '../components/Mixins.js'
  import ErrorMessage from '../components/ErrorMessage.vue'
  import RemoveRequestedTaskButton from '../components/RemoveRequestedTaskButton.vue'
  import ResourceBadge from '../components/ResourceBadge.vue'
  import TaskLink from '../components/TaskLink.vue'

  export default {
    name: 'PipelineTable',
    mixins: [ZimfarmMixins],
    components: {ErrorMessage, RemoveRequestedTaskButton, ResourceBadge, TaskLink},
    props: {
      selectedTable: String, // applied filter: todo, doing, done, failed
    },
    data() {
      return {
        tasks: [], // list of tasks returned by API
        meta: {}, // API query metadata (count, skip, limit)
        error: false, // error string to display on API error
        timer: null,  // auto-refresh timer
        loading: false,
        schedules_last_runs: {}, // last runs for all schedule_names of tasks
        last_runs_loaded: false,  // used to trigger render() on last_run cell
      };
    },
    computed: {
      total_results() { // total (non-paginated) tasks for query from API
        return (this.meta && this.meta.count) ? this.meta.count : 0;
      }
    },
    methods: {
      getPropFor(schedule_name, prop, otherwise) {
        let last_run = this.schedules_last_runs[schedule_name];
        if (last_run)
          if (last_run[prop])
            return last_run[prop];
        if (otherwise)
          return otherwise;
        return null;
      },
      limitChanged() {
        this.saveLimitPreference(this.selectedLimit);
        this.loadData();
      },
      resetData() { // reset data holders
        this.error = null;
        this.tasks = [];
        this.meta = {};
        this.loading = false;
      },
      loadGenericData(url, params, item_transform, success_callback) {
        let parent = this;
        parent.toggleLoader("fetching tasks…");
        parent.loading = true;
        this.queryAPI('get', url, {params})
          .then(function (response) {
              parent.resetData();
              parent.meta = response.data.meta;
              parent.tasks = response.data.items.map(item_transform);
              if (success_callback)
                success_callback();
          })
          .catch(function (error) {
            parent.resetData();
            parent.error = Constants.standardHTTPError(error.response);
          })
          .then(function () {
              parent.toggleLoader(false);
          });
      },
      loadData() {
        let parent = this;
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
                                item["duration"] = Constants.format_duration_between(item.timestamp.started, item.updated_at);
                                return item;
                               });
        }
        if (this.selectedTable == 'failed') {
          this.loadGenericData('/tasks/',
                               {limit: this.selectedLimit,
                                status: ["scraper_killed", "failed", "canceled"]},
                               function (item) {
                                item["duration"] = Constants.format_duration_between(item.timestamp.started, item.updated_at);
                                return item;
                               }, function(){ // success_callback
                                parent.loadLastRuns();
                               });
        }
      },
      async loadLastRuns() {
        let parent = this;
        let schedule_names = parent.tasks.map(function (item) { return item.schedule_name; }).unique();

        parent.toggleLoader("fetching tasks…");
        let requests = schedule_names.map(function (schedule_name) {
            return parent.queryAPI('get', "/schedules/" + schedule_name);
          });
        let results = await axios.all(requests);

        results.forEach(function (response, index) {
          let schedule_name = schedule_names[index];
          if (response.data.most_recent_task) {
           parent.schedules_last_runs[schedule_name] = response.data.most_recent_task;
          }
        });
        parent.last_runs_loaded = true;
        parent.toggleLoader(false);
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
