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
          <th @click="sortBy('schedule_name')" class="sortable">
            Schedule
            <span v-if="sortColumn === 'schedule_name'" class="sort-icon">{{ sortOrder === 'asc' ? '▲' : '▼' }}</span>
          </th>
          <th @click="sortBy('timestamp.requested')" class="sortable">
            Requested
            <span v-if="sortColumn === 'timestamp.requested'" class="sort-icon">{{ sortOrder === 'asc' ? '▲' : '▼' }}</span>
          </th>
          <th @click="sortBy('requested_by')" class="sortable">
            By
            <span v-if="sortColumn === 'requested_by'" class="sort-icon">{{ sortOrder === 'asc' ? '▲' : '▼' }}</span>
          </th>
          <th>Resources</th>
          <th @click="sortBy('worker')" class="sortable">
            Worker
            <span v-if="sortColumn === 'worker'" class="sort-icon">{{ sortOrder === 'asc' ? '▲' : '▼' }}</span>
          </th>
          <th v-show="canUnRequestTasks">Remove</th>
        </tr>
      </thead>
      <thead v-if="selectedTable == 'doing'">
        <tr>
          <th @click="sortBy('schedule_name')" class="sortable">
            Schedule
            <span v-if="sortColumn === 'schedule_name'" class="sort-icon">{{ sortOrder === 'asc' ? '▲' : '▼' }}</span>
          </th>
          <th @click="sortBy('timestamp.reserved')" class="sortable">
            Started
            <span v-if="sortColumn === 'timestamp.reserved'" class="sort-icon">{{ sortOrder === 'asc' ? '▲' : '▼' }}</span>
          </th>
          <th @click="sortBy('worker')" class="sortable">
            Worker
            <span v-if="sortColumn === 'worker'" class="sort-icon">{{ sortOrder === 'asc' ? '▲' : '▼' }}</span>
          </th>
        </tr>
      </thead>
      <thead v-if="selectedTable == 'done'">
        <tr>
          <th @click="sortBy('schedule_name')" class="sortable">
            Schedule
            <span v-if="sortColumn === 'schedule_name'" class="sort-icon">{{ sortOrder === 'asc' ? '▲' : '▼' }}</span>
          </th>
          <th @click="sortBy('updated_at')" class="sortable">
            Completed
            <span v-if="sortColumn === 'updated_at'" class="sort-icon">{{ sortOrder === 'asc' ? '▲' : '▼' }}</span>
          </th>
          <th @click="sortBy('worker')" class="sortable">
            Worker
            <span v-if="sortColumn === 'worker'" class="sort-icon">{{ sortOrder === 'asc' ? '▲' : '▼' }}</span>
          </th>
          <th>
            Duration
          </th>
        </tr>
      </thead>
      <thead v-if="selectedTable == 'failed'">
        <tr>
          <th @click="sortBy('schedule_name')" class="sortable">
            Schedule
            <span v-if="sortColumn === 'schedule_name'" class="sort-icon">{{ sortOrder === 'asc' ? '▲' : '▼' }}</span>
          </th>
          <th @click="sortBy('updated_at')" class="sortable">
            Stopped
            <span v-if="sortColumn === 'updated_at'" class="sort-icon">{{ sortOrder === 'asc' ? '▲' : '▼' }}</span>
          </th>
          <th @click="sortBy('worker')" class="sortable">
            Worker
            <span v-if="sortColumn === 'worker'" class="sort-icon">{{ sortOrder === 'asc' ? '▲' : '▼' }}</span>
          </th>
          <th>
            Duration
          </th>
          <th @click="sortBy('status')" class="sortable">
            Status
            <span v-if="sortColumn === 'status'" class="sort-icon">{{ sortOrder === 'asc' ? '▲' : '▼' }}</span>
          </th>
          <th>Last Run</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="task in tasks" :key="task._id">
          <td v-if="task.schedule_name === null || task.schedule_name == 'none'">{{ task.original_schedule_name }}</td>
          <td v-else><router-link :to="{name: 'schedule-detail', params: {schedule_name: task.schedule_name}}">{{ task.schedule_name }}</router-link></td>
          <td v-if="selectedTable == 'todo'"
              v-tooltip="{content: format_dt(task.timestamp.requested), delay: 10}">{{ task.timestamp.requested | from_now }}</td>
          <td v-if="selectedTable == 'todo'">{{ task.requested_by }}</td>
          <td v-if="selectedTable == 'todo'"><ResourceBadge kind="cpu" :value="task.config.resources.cpu" />
              <ResourceBadge kind="memory" :value="task.config.resources.memory" />
              <ResourceBadge kind="disk" :value="task.config.resources.disk" /></td>
          <td v-if="selectedTable == 'doing'"
              v-tooltip="{content: format_dt(task.timestamp.reserved), delay: 10}">
              <router-link :to="{name: 'task-detail', params: {_id: task._id}}">{{ task.timestamp.reserved | from_now }}</router-link>
          </td>
          <td v-if="selectedTable == 'done'"
              v-tooltip="{content: format_dt(task.updated_at), delay: 10}">
              <router-link :to="{name: 'task-detail', params: {_id: task._id}}">{{ task.updated_at | from_now }}</router-link>
          </td>
          <td v-if="selectedTable == 'failed'"
              v-tooltip="{content: format_dt(task.updated_at), delay: 10}">
              <router-link :to="{name: 'task-detail', params: {_id: task._id}}">{{ task.updated_at | from_now }}</router-link>
          </td>
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
        sortColumn: null,
        sortOrder: 'desc',
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
        if (this.sortColumn) {
          params.sort_by = this.sortColumn;
          params.sort_order = this.sortOrder;
          if (params.sort) delete params.sort;
          if (params.order) delete params.order;
        }
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
            parent.standardErrorHandling(error);
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
                                status: ["reserved", "started", "scraper_started", "scraper_completed", "cancel_requested"]},
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
        parent.last_runs_loaded = false;
        let schedule_names = parent.tasks.map(function (item) { return item.schedule_name; }).unique();

        parent.toggleLoader("fetching last runs…");
        const chunkSize = Constants.TASKS_LOAD_SCHEDULES_CHUNK_SIZE;
        let requests = []
        for (let i = 0; i < schedule_names.length; i += chunkSize) {
            const chunk = schedule_names.slice(i, i + chunkSize);
            for (let iChunk in chunk) {
              requests.push(parent.queryAPI('get', "/schedules/" + chunk[iChunk]))
            }
            await Constants.getDelay(Constants.TASKS_LOAD_SCHEDULES_DELAY)
        }

        const results = await Promise.all(requests.map(p => p.catch(e => e)));

        results.forEach(function (response, index) {
          if (!(response instanceof Error)) {
            let schedule_name = schedule_names[index];
            if (response.data.most_recent_task) {
             parent.schedules_last_runs[schedule_name] = response.data.most_recent_task;
            }
          }
        });
        parent.last_runs_loaded = true;
        parent.toggleLoader(false);
      },
      sortBy(column) {
        if (this.sortColumn === column) {
          this.sortOrder = this.sortOrder === 'asc' ? 'desc' : 'asc';
        } else {
          this.sortColumn = column;
          this.sortOrder = 'desc';
        }
        this.loadData();
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
<style>
.sortable {
  cursor: pointer;
  position: relative;
  user-select: none;
}
.sortable:hover {
  background-color: rgba(0, 0, 0, 0.05);
}
.sort-icon {
  margin-left: 5px;
  font-size: 0.8em;
}
</style>
