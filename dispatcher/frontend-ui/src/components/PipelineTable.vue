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
        <tr><th>Schedule</th><th>Requested</th><th>By</th><th v-show="$store.getters.isLoggedIn">Remove</th></tr>
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
            {{ task.schedule_name }}
            <span class="text-warning" v-if="task.priority > 0"> <font-awesome-icon size="sm" icon="fire" /></span>
          </td>
          <td v-if="selectedTable == 'todo'"
              v-tooltip="{content: format_dt(task.requested_on), delay: 10}">{{ task.requested_since }}</td>
          <td v-if="selectedTable == 'todo'">{{ task.requested_by }}</td>
          <td v-if="selectedTable == 'doing'"
              v-tooltip="{content: format_dt(task.started_on), delay: 10}">{{ task.started_since }}</td>
          <td v-if="selectedTable == 'done' || selectedTable == 'failed'"
              v-tooltip="{content: format_dt(task.completed_on), delay: 10}">{{ task.completed_since }}</td>
          <td v-if="selectedTable != 'todo'">{{ task.worker }}</td>
          <td v-if="selectedTable == 'done' || selectedTable == 'failed'">{{ task.duration }}</td>
          <td v-if="selectedTable == 'failed'">{{ task.status }}</td>
          <td v-if="selectedTable == 'todo'" v-show="$store.getters.isLoggedIn"><RemoveRequestedTaskButton :_id="task._id" @requestedtasksremoved="loadData" /></td>
        </tr>
      </tbody>
    </table>
    <ErrorMessage :message="error" v-else />
  </div>
</template>

<script type="text/javascript">
  import moment from 'moment';

  import Constants from '../constants.js'
  import ZimfarmMixins from './Mixins.js'
  import ErrorMessage from './ErrorMessage.vue'
  import RemoveRequestedTaskButton from './RemoveRequestedTaskButton.vue'

  export default {
    name: 'PipelineTable',
    mixins: [ZimfarmMixins],
    components: {ErrorMessage, RemoveRequestedTaskButton},
    props: {
      selectedTable: String, // applied filter: todo, doing, done, failed
    },
    data() {
      return {
        tasks: [], // list of tasks returned by API
        meta: {}, // API query metadata (count, skip, limit)
        error: false, // error string to display on API error
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

              for (var i=0; i<response.data.items.length; i++){
                let item = response.data.items[i];
                parent.tasks.push(item_transform(item));
              }
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
                               function (item) {
                                item["requested_on"] = moment(item["timestamp"]["requested"])
                                item["requested_since"] = item["requested_on"].fromNow();
                                return item;
                               });
        }
        if (this.selectedTable == 'doing') {
          this.loadGenericData('/tasks/',
                               {limit: this.selectedLimit,
                                status: ["reserved", "started", "scraper_started", "cancel_requested"]},
                               function (item) {
                                item["started_on"] = moment(item["timestamp"]["started"])
                                item["started_since"] = item["started_on"].fromNow();
                                return item;
                               });
        }
        if (this.selectedTable == 'done') {
          this.loadGenericData('/tasks/',
                               {limit: this.selectedLimit,
                                status: ["succeeded"]},
                               function (item) {
                                item["completed_on"] = moment(item["timestamp"]["succeeded"])
                                item["completed_since"] = item["completed_on"].fromNow();
                                item["duration"] = Constants.format_duration_between(item.timestamp.started, item["completed_on"]);
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
                                item["completed_on"] = moment(event_ts);
                                item["completed_since"] = item["completed_on"].fromNow();
                                item["duration"] = Constants.format_duration_between(item.timestamp.started, item["completed_on"]);
                                return item;
                               });
        }
      },
    },
    mounted() {
      this.loadData();
    },
    watch: {
      selectedTable() {
        this.loadData();
      },
    }
  };
</script>
