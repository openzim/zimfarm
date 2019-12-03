<!-- Task Detail View
  - listing all info
  - fire schedule button -->

<template>
  <div class="container">
    <BackButton class="mb-2" />
    <h1><code>#{{ short_id }}</code></h1>
    <div v-if="!error">
      <ul class="nav nav-tabs">
        <li class="nav-item"><a href="#" class="nav-link" :class="{ active: selectedTab == 'details'}" @click.prevent="selectedTab='details'">Task</a></li>
        <li class="nav-item"><a href="#" class="nav-link" :class="{ active: selectedTab == 'container'}" @click.prevent="selectedTab='container'">Container</a></li>
        <li class="nav-item"><a href="#" class="nav-link" :class="{ active: selectedTab == 'debug'}" @click.prevent="selectedTab='debug'">Debug</a></li>
      </ul>

      <div v-if=" selectedTab == 'details'" class="details">
        <table class="table table-responsive-sm table-striped">
          <tr><th>ID</th><td><code>{{ this._id }}</code></td></tr>
          <tr><th>Schedule</th><td><router-link :to="{name: 'schedule-detail', params: {schedule_name: task.schedule_name}}">{{ task.schedule_name}}</router-link> <FireScheduleButton :name="task.schedule_name" /></td></tr>
          <tr><th>Status</th><td><code>{{ task.status }}</code></td></tr>
          <tr><th>Worker</th><td>{{ task.worker }}</td></tr>
          <tr><th>Duration</th><td>{{ task_duration }}</td></tr>
        </table>
        <h3>Events</h3>
        <ul>
          <li v-for="event in task.events" v-bind:key="event.code"><code>{{ event.code }}</code>: {{ event.timestamp | datetime }}</li>
        </ul>
        <div v-if="task.files">
          <h3>Files</h3>
          <table class="table table-responsive-sm table-striped">
            <thead><tr><th>Filename</th><th>Size</th><th>Created After</th><th>Upload Duration</th></tr></thead>
            <tr v-for="file in task.files" :key="file.name">
              <td><a target="_blank" :href="kiwix_download_url + task.config.warehouse_path + '/' + file.name">{{ file.name}}</a></td>
              <td>{{ file.size | filesize }}</td>
              <td v-tooltip="datetime(file.created_timestamp)">{{ file | created_after(task) }}</td>
              <td v-tooltip="datetime(file.uploaded_timestamp)" v-if="file.status == 'uploaded'">{{ file | upload_duration }}</td>
              <td v-else>-</td>
            </tr>
          </table>
        </div>
      </div>
      <div v-if="selectedTab == 'container'" class="details">
        <div v-if="task.container">
          <div v-if="task.container.image">
            <h3>Image</h3>
            <p>{{ task.container.image }}</p>
          </div>
          <div v-if="task.container.command">
            <h3>Command</h3>
            <code>{{ task.container.command }}</code>
          </div>
          <div v-if="task.container.exit_code">
            <h3>Exit-code</h3>
            <code>{{ task.container.exit_code }}</code>
          </div>
          <div v-if="task.container.log">
            <h3>Log</h3>
            <a target="_blank" :href="zimfarm_logs_url + '/' + task.container.log">{{ task.container.log }}</a>
          </div>
        </div>
      </div>

      <div v-if="selectedTab == 'debug'" class="details">
        <div v-if="task.debug">
          <div v-if="task.debug.exception">
            <h3>Exception</h3>
            <pre>{{ task.debug.exception }}</pre>
          </div>
          <div v-if="task.debug.traceback">
            <h3>Traceback</h3>
            <pre>{{ task.debug.traceback }}</pre>
          </div>
          <div v-if="task.debug.log">
            <h3>Task worker Log</h3>
            <pre>{{ task.debug.log }}</pre>
          </div>
        </div>
      </div>

    </div>
    <ErrorMessage v-bind:message="error" v-else />
  </div>
</template>

<script>
  import Constants from '../constants.js'
  import ZimfarmMixins from '../components/Mixins.js'
  import ErrorMessage from '../components/ErrorMessage.vue'
  import BackButton from '../components/BackButton.vue'
  import FireScheduleButton from '../components/FireScheduleButton.vue'


  export default {
    name: 'TaskView',
    mixins: [ZimfarmMixins],
    components: {FireScheduleButton, ErrorMessage, BackButton},
    props: {
      _id: String,
    },
    data() {
      return {
        task: {}, // the retrieved task from API
        error: false, // error message to display on API error
        selectedTab: 'details',  // currently selected tab: details, container, debug
      };
    },
    filters: {
      created_after(value, task) {
        return Constants.duration_between(task.timestamp.scraper_started, value.created_timestamp);
      },
      upload_duration(value) {
        return Constants.duration_between(value.created_timestamp, value.uploaded_timestamp);
      }
    },
    computed: {
      short_id() {
        return this._id.substr(this._id.length - 5);
      },
      task_duration() {
        if (!this.task.events)
          return '';
        let last = this.task.events[this.task.events.length - 1].timestamp;
        let first = this.task.timestamp.started;
        return Constants.duration_between(first, last);
      },
      zimfarm_logs_url() { return Constants.zimfarm_logs_url; },
      kiwix_download_url() { return Constants.kiwix_download_url; },
    },
    methods: {
      datetime(value) {  // shortcut datetime formatter
        return Constants.datetime(value);
      }
    },
    mounted() {
      let parent = this;

      parent.toggleLoader("fetching task…");
      parent.$root.axios.get('/tasks/' + this._id, {})
        .then(function (response) {
            parent.error = null;
            parent.task = response.data;
        })
        .catch(function (error) {
          parent.error = Constants.standardHTTPError(error.response);
        })
        .then(function () {
            parent.toggleLoader(false);
        });
    },
  }
</script>

<style type="text/css" scoped>
  .details {
    background-color: white;
    padding: .5rem;
    border: 1px solid #dee2e6;
    border-top: 0;
  }
</style>
