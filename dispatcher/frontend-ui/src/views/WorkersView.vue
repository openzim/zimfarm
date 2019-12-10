<!-- Placeholder view for listing workers and their current statuses: needs API update -->

<template>
  <div class="container">
    <div class="row mb-2" v-show="!error && ready">
      <div class="col progress-col">
        <b-progress>
          <b-progress-bar
            :value="current_memory"
            :max="max_memory"
            :variant="progress_class"
            :label="overall_progress + '%'"
            show-progress
            animated>
            </b-progress-bar>
        </b-progress>
      </div>
      <div class="col">
        <span class="badge badge-light mr-2"><font-awesome-icon icon="plug" /> {{ online_workers.length }}</span>
        <ResourceBadge kind="cpu" :human_value="usage_cpu" />
        <ResourceBadge kind="memory" :human_value="usage_memory" />
        <ResourceBadge kind="disk" :human_value="usage_disk" />
        <b-button class="toggle_btn"
                  variant="outline-secondary btn-sm"
                  @click.prevent="toggle_workerslist">{{ toggle_text }}</b-button>
      </div>
    </div>
    <table v-if="!error && workers" class="table table-responsive-sm">
      <tbody>
        <tr v-for="worker in workers" :key="worker.name" :class="(worker.status == 'online') ? 'alert-success' : 'alert-warning'">
          <th>{{ worker.name }}</th>
          <td colspan="2" v-if="worker.status == 'online' && worker.tasks">
            <table class="table table-sm table-responsive-sm table-striped table-hover">
              <tbody>
                <tr>
                  <th colspan="2" class="text-right">Worker Resources</th>
                  <td><ResourceBadge kind="cpu" :value="worker.resources.cpu" /></td>
                  <td><ResourceBadge kind="memory" :value="worker.resources.memory" /></td>
                  <td><ResourceBadge kind="disk" :value="worker.resources.disk" /></td>
                </tr>
                <tr v-for="task in worker.tasks" :key="task._id">
                  <td>{{ task.schedule_name }}</td>
                  <td v-tooltip="format_dt(started_on(task))">{{ started_on(task)|from_now }}</td>
                  <td><ResourceBadge kind="cpu" :value="task.config.resources.cpu" /></td>
                  <td><ResourceBadge kind="memory" :value="task.config.resources.memory" /></td>
                  <td><ResourceBadge kind="disk" :value="task.config.resources.disk" /></td>
                </tr>
              </tbody>
            </table>
          </td>
          <td v-if="worker.status == 'offline' || !worker.tasks">{{ worker.status }}</td>
          <td v-if="worker.status == 'offline' || !worker.tasks" v-tooltip="format_dt(worker.last_seen)">{{ worker.last_seen|from_now }}</td>
        </tr>
      </tbody>
    </table>
    <ErrorMessage :message="error" v-else />
  </div>
</template>

<script type="text/javascript">
  import filesize from 'filesize';

  import Constants from '../constants.js'
  import ZimfarmMixins from '../components/Mixins.js'
  import ErrorMessage from '../components/ErrorMessage.vue'
  import ResourceBadge from '../components/ResourceBadge.vue'

  export default {
    name: 'WorkersView',
    mixins: [ZimfarmMixins],
    components: {ErrorMessage, ResourceBadge},
    data() {
      return {
        ready: false,
        showing_all: true,  // toggle switch for list of workers
        error: null,  // API generated error
        all_workers: [],  // list of workers as returned by API
        running_tasks: [],  // running tasks returned by API
      };
    },
    computed: {
      toggle_text() { return this.showing_all ? 'Show Onlines Only' : 'Show All'; },
      workers() { return this.showing_all ? this.all_workers : this.online_workers; },
      online_workers() { return this.all_workers.filter(function (worker) { return worker.status == "online"; }); },
      workers_names() {
        return this.workers.map(function (worker) { return worker.name; });
      },
      tasks() { // filtered list of running tasks matching our workers list
        let parent = this;
        return parent.running_tasks.filter(function(task) { return parent.workers_names.indexOf(task.worker) != -1; });
      },
      progress_class() {
        if (this.overall_progress <= 10 || this.overall_progress > 100)
          return 'danger';
        if (this.overall_progress <= 50)
          return 'warning';
        if (this.overall_progress <= 70)
          return 'info';
        return 'success';
      },
      max_cpu() {
        return this.online_workers.reduce(function(a, b) { return a + b.resources.cpu; }, 0);
      },
      max_memory() {
        return this.online_workers.reduce(function(a, b) { return a + b.resources.memory; }, 0);
      },
      max_disk() {
        return this.online_workers.reduce(function(a, b) { return a + b.resources.disk; }, 0);
      },
      current_cpu() {
        return this.tasks.reduce(function(a, b) { return a + b.config.resources.cpu; }, 0);
      },
      current_memory() {
        return this.tasks.reduce(function(a, b) { return a + b.config.resources.memory; }, 0);
      },
      current_disk() {
        return this.tasks.reduce(function(a, b) { return a + b.config.resources.disk; }, 0);
      },
      usage_cpu() {
        return this.current_cpu + "/" + this.max_cpu;
      },
      usage_memory() {
        return filesize(this.current_memory) + "/" + filesize(this.max_memory);
      },
      usage_disk() {
        return filesize(this.current_disk) + "/" + filesize(this.max_disk);
      },
      overall_progress() {
        return this.max_memory ? (this.current_memory * 100 / this.max_memory).toFixed(0) : 0;
      },
    },
    methods: {
      started_on(task) {
        return task.timestamp.started || "not started";
      },
      toggle_workerslist() { this.showing_all = !this.showing_all; },
      addToWorker(task) {
        for (var i=0; i<this.all_workers.length; i++){
          if (this.all_workers[i].name == task.worker) {
            this.all_workers[i].tasks.push(task);
            return;
          }
        }
      },
      loadRunningTasks() {
        let parent = this;

        parent.toggleLoader("fetching tasks…");
        parent.$root.axios.get('/tasks/', {params: {status: Constants.running_statuses}})
          .then(function (response) {
            parent.error = null;
            parent.running_tasks = [];
            for (var i=0; i<response.data.items.length; i++){
              let task = response.data.items[i];
              parent.addToWorker(task);
              parent.running_tasks.push(task);
            }

          })
          .catch(function (error) {
            parent.error = Constants.standardHTTPError(error.response);
          })
          .then(function () {
            parent.toggleLoader(false);
            parent.ready = true;
          });
      },
      loadWorkersList() {  // load workers list from API
        let parent = this;

        parent.toggleLoader("fetching workers…");
        parent.$root.axios.get('/workers/')
          .then(function (response) {
            parent.error = null;
            parent.all_workers = [];
            for (var i=0; i<response.data.items.length; i++){
              response.data.items[i].tasks = []; // placeholder for tasks
              parent.all_workers.push(response.data.items[i]);
            }
            parent.loadRunningTasks();
          })
          .catch(function (error) {
            parent.error = Constants.standardHTTPError(error.response);
          })
          .then(function () {
            parent.toggleLoader(false);
          });
      },
    },
    mounted() {
      this.loadWorkersList();
    },
  }
</script>

<style type="text/css">
  .col { line-height: unset; }
  .progres-col { line-height: 0; }
  .progress { height: 100%; }
  .toggle_btn { float: right; }
</style>
