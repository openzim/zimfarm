<!-- Task Detail View
  - listing all info
  - fire schedule button -->

<template>
  <div class="container">
    <div class="row"><ScheduleActionButton v-if="task" :name="schedule_name" /></div>
    <h2 class="row">
      <span class="col col-xs-12 col-sm-4 col-md-3 col-lg-2"><code>#{{ short_id }}</code></span>
      <span class="col col-xs-12 col-sm-8 col-md-9 col-lg-10" v-if="schedule_name"><code>{{ schedule_name }}</code></span>
    </h2>
    <div v-if="!error && task">
      <ul class="nav nav-tabs">
        <li class="nav-item" :class="{ active: selectedTab == 'details'}">
          <router-link class="nav-link"
                       active-class="dummy"
                       :class="{ active: selectedTab == 'details'}"
                       :to="{name: 'task-detail', params: {_id: _id}}">
            Info
          </router-link>
        </li>
        <li class="nav-item" :class="{ active: selectedTab == 'debug'}">
          <router-link class="nav-link"
                       active-class="dummy"
                       :class="{ active: selectedTab == 'debug'}"
                       :to="{name: 'task-detail-tab', params: {_id: _id, selectedTab: 'debug'}}">
            Debug
          </router-link>
        </li>
      </ul>

      <div v-if=" selectedTab == 'details'" class="tab-content">
        <table class="table table-responsive-md table-striped table-in-tab">
          <tr><th>ID</th><td><code>{{ _id }}</code>, <a target="_blank" :href="webapi_url + '/tasks/' + _id">document <font-awesome-icon icon="external-link-alt" size="sm" /></a></td></tr>
          <tr>
            <th>Recipe</th>
            <td><router-link :to="{name: 'schedule-detail', params: {schedule_name: task.schedule_name}}">
              {{ task.schedule_name}}
              </router-link>
            </td>
          </tr>
          <tr><th>Status</th><td><code>{{ task.status }}</code></td></tr>
          <tr><th>Worker</th><td>{{ task.worker }}</td></tr>
          <tr><th>Started On</th><td>{{ started_on|format_dt }}, after <strong>{{ pipe_duration }} in pipe</strong></td></tr>
          <tr><th>Duration</th><td>{{ task_duration }}<span v-if="is_running"> (<strong>Ongoing</strong>)</span></td></tr>
          <tr>
            <th>Events</th>
            <td>
              <table class="table table-responsive-md table-striped table-sm">
              <tbody>
              <tr v-for="event in task.events" v-bind:key="event.code">
                <td><code>{{ event.code }}</code></td><td>{{ event.timestamp | format_dt }}</td>
              </tr>
              </tbody>
            </table>
            </td>
          </tr>
          <tr v-if="task.files">
            <th>Files</th>
            <td>
              <table class="table table-responsive-md table-striped table-sm">
                <thead><tr><th>Filename</th><th>Size</th><th>Created After</th><th>Upload Duration</th></tr></thead>
                <tr v-for="file in task.files" :key="file.name">
                  <td><a target="_blank" :href="kiwix_download_url + task.config.warehouse_path + '/' + file.name">{{ file.name}}</a></td>
                  <td>{{ file.size | filesize }}</td>
                  <td v-tooltip="format_dt(file.created_timestamp)">{{ file | created_after(task) }}</td>
                  <td v-tooltip="format_dt(file.uploaded_timestamp)" v-if="file.status == 'uploaded'">{{ file | upload_duration }}</td>
                  <td v-else>-</td>
                </tr>
              </table>
            </td>
          </tr>
        </table>
      </div>
      <div v-if="selectedTab == 'debug'" class="tab-content">
        <table class="table table-responsive table-striped table-in-tab">
          <tr v-if="task.config"><th>Offliner</th><td>{{ task.config.task_name }}</td></tr>
          <tr v-if="task.config"><th>Config</th><td><FlagsList :flags="task.config.flags" :shrink="true" /></td></tr>
          <tr v-if="task_container.command"><th>Command <button class="btn btn-light btn-sm" @click.prevent="copyCommand"><font-awesome-icon icon="copy" size="sm" /> Copy</button></th><td><code class="command">{{ command }}</code></td></tr>
          <tr v-if="task_container.exit_code != null"><th>Exit-code</th><td><code>{{ task_container.exit_code }}</code></td></tr>
          <tr v-if="task_container.stdout"><th>Scraper&nbsp;stdout</th><td><pre class="stdout">{{ task_container.stdout }}</pre></td></tr>
          <tr v-if="task_container.stderr"><th>Scraper&nbsp;stderr</th><td><pre class="stderr">{{ task_container.stderr }}</pre></td></tr>
          <tr v-if="task_container.log"><th>Scrapper&nbsp;Log</th><td><a class="btn btn-secondary btn-sm" target="_blank" :href="zimfarm_logs_url + '/' + task_container.log">Download log</a></td></tr>
          <tr v-if="task_debug.exception"><th>Exception</th><td><pre>{{ task_debug.exception }}</pre></td></tr>
          <tr v-if="task_debug.traceback"><th>Traceback</th><td><pre>{{ task_debug.traceback }}</pre></td></tr>
          <tr v-if="task_debug.log"><th>Task-worker Log</th><td><pre>{{ task_debug.log }}</pre></td></tr>
        </table>
      </div>

    </div>
    <ErrorMessage v-bind:message="error" v-if="error" />
  </div>
</template>

<script>
  import Constants from '../constants.js'
  import ZimfarmMixins from '../components/Mixins.js'
  import ErrorMessage from '../components/ErrorMessage.vue'
  import ScheduleActionButton from '../components/ScheduleActionButton.vue'
  import FlagsList from '../components/FlagsList.vue'


  export default {
    name: 'TaskView',
    mixins: [ZimfarmMixins],
    components: {ScheduleActionButton, ErrorMessage, FlagsList},
    props: {
      _id: String,
      selectedTab: {
        type: String,
        default: 'details',  // currently selected tab: details, container, debug
      }
    },
    data() {
      return {
        task: null, // the retrieved task from API
        error: false, // error message to display on API error
      };
    },
    filters: {
      created_after(value, task) {
        return Constants.format_duration_between(task.timestamp.scraper_started, value.created_timestamp);
      },
      upload_duration(value) {
        return Constants.format_duration_between(value.created_timestamp, value.uploaded_timestamp);
      }
    },
    computed: {
      short_id() { return Constants.short_id(this._id); },
      is_running() { return ["failed", "canceled", "succeeded"].indexOf(this.task.status) == -1; },
      schedule_name() { return this.task ? this.task.schedule_name : null; },
      task_container() { return this.task.container || {}; },
      task_debug() { return this.task.debug || {}; },
      task_duration() {  // duration of a task
        if (!this.task.events)
          return '';

        let first = this.task.timestamp.started;
        if (!first)  // probably in reserved state, hence not yet started
          return "not actually started";

        // if task is running (non-complete status) then it's started-to now
        if (this.is_running) {
          return Constants.format_duration_between(first, Constants.now());
        }

        // if task is not running, it's started to last status
        let last = this.task.updated_at;
        return Constants.format_duration_between(first, last);
      },
      started_on() { return this.task.timestamp.started || this.task.timestamp.reserved; },
      pipe_duration() { return Constants.format_duration_between(this.task.timestamp.requested, this.task.timestamp.started); },
      zimfarm_logs_url() { return Constants.zimfarm_logs_url; },
      kiwix_download_url() { return Constants.kiwix_download_url; },
      webapi_url() { return Constants.zimfarm_webapi; },
      command() { return this.task_container.command.join(" "); },
      trimmed_command() { return Constants.trim_command(this.command); },
    },
    methods: {
      copyCommand() {
        let parent = this;
        this.$copyText(this.command).then(function () {
            parent.alertInfo("Command copied to Clipboard!");
          }, function () {
            parent.alertWarning("Unable to copy command to clipboard 😞. ",
                                "Please copy it manually.");
          });
      }
    },
    mounted() {
      let parent = this;

      parent.toggleLoader("fetching task…");
      parent.queryAPI('get', '/tasks/' + this._id, {})
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
    updated(){
      // scroll stdout and stderr to bottom
      let element;
      ["stdout", "stderr"].forEach(function(item) {
        element = this.$el.querySelector("." + item);
        if (element)
          element.scrollTop = element.scrollHeight;
      }.bind(this));

    }
  }
</script>

<style type="text/css">
  .stdout, .stderr {
    max-height: 9rem;
    overflow: scroll;
  }
</style>
