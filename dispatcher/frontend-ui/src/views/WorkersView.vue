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
    <table v-if="!error && workers" class="table table-responsive-md table-sm table-striped table-hover">
      <tbody>
        <tr v-for="row in rows" :key="row.id" >
          <th v-if="row.kind == 'worker'"
              :rowspan="row.rowspan"
              class="bg-light"
              :class="(row.status == 'online') ? 'text-success' : 'text-secondary'">{{ row.worker.name }}</th>


          <td v-show="row.status == 'offline'" v-if="row.kind == 'worker'" colspan="1" v-tooltip="format_dt(row.worker.last_seen)">
            <font-awesome-icon icon="skull-crossbones" /> {{ row.worker.last_seen | from_now}}
          </td>
          <th v-show="row.status == 'offline'" v-if="row.kind == 'worker'" colspan="1" class="text-right">Resources</th>
          <th v-show="row.status == 'online'" v-if="row.kind == 'worker'" colspan="2" class="text-right">Resources</th>

          <th v-if="row.kind == 'worker'" class="text-center">
            <ResourceBadge kind="cpu" :value="row.worker.resources.cpu" />
          </th>
          <th v-if="row.kind == 'worker'" class="text-center">
            <ResourceBadge kind="memory" :value="row.worker.resources.memory" />
          </th>
          <th v-if="row.kind == 'worker'" class="text-center">
            <ResourceBadge kind="disk" :value="row.worker.resources.disk" />
          </th>
          <td v-if="row.kind == 'task'">
            <router-link :to="{name: 'schedule-detail', params:{schedule_name: row.task.schedule_name}}">
              {{ row.task.schedule_name }}
            </router-link>
          </td>
          <td v-if="row.kind == 'task'">
            <TaskLink :_id="row.task._id" :updated_at="started_on(row.task)" />
          </td>
          <td v-if="row.kind == 'task'" class="text-center">{{ row.task.config.resources.cpu }}</td>
          <td v-if="row.kind == 'task'" class="text-center">{{ row.task.config.resources.memory|filesize }}</td>
          <td v-if="row.kind == 'task'" class="text-center">{{ row.task.config.resources.disk|filesize }}</td>
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
  import TaskLink from '../components/TaskLink.vue'

  export default {
    name: 'WorkersView',
    mixins: [ZimfarmMixins],
    components: {ErrorMessage, ResourceBadge, TaskLink},
    data() {
      return {
        ready: false,
        showing_all: null,  // toggle switch for list of workers
        error: null,  // API generated error
        all_workers: [],  // list of workers as returned by API
        running_tasks: [],  // running tasks returned by API
        timer: null,  // auto-refresh data timer
      };
    },
    computed: {
      rows() {  // special list of `rows` to handle table with rowspans
        let table_rows = [];
        for (var i=0; i<this.workers.length; i++) {
          let worker = this.workers[i];
          let status = worker.status;
          let rowspan = 1 + worker.tasks.length;
          table_rows.push({
              kind: "worker",
              id: worker.name,
              status: status,
              rowspan: rowspan,
              worker: worker,
            });
          for (var ii=0; ii<worker.tasks.length; ii++) {
            let task = worker.tasks[ii];
            table_rows.push({
              kind: "task",
              id:task._id,
              status: status,
              rowspan: 1,
              task: task,
            });
          }
        }
        return table_rows;
      },
      toggle_text() { return this.showing_all ? 'Hide Offlines' : 'Show All'; },
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
      getOnlinesOnlyPreference() {   // retrieve onlines-only value from cookie
        let value = JSON.parse(this.$cookie.get('onlines-only'));
        if (value === null)
          value = false; // default state
        return value;
      },
      saveOnlinesOnlyPreference(value) {  // save onlines-only pref into cookie
        this.$cookie.set('onlines-only', JSON.stringify(value));
      },
      started_on(task) {
        return task.timestamp.started || "not started";
      },
      toggle_workerslist() {
        this.showing_all = !this.showing_all;
        this.saveOnlinesOnlyPreference(!this.showing_all);
      },
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
        parent.queryAPI('get', '/tasks/', {params: {status: Constants.running_statuses, limit:200}})
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
        parent.queryAPI('get', '/workers/')
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
      this.showing_all = !this.getOnlinesOnlyPreference();
      this.loadWorkersList();
      this.timer = setInterval(this.loadWorkersList, 60000);
    },
    beforeDestroy () {
      clearInterval(this.timer)
    }
  }
</script>

<style type="text/css">
  .col { line-height: unset; }
  .progres-col { line-height: 0; }
  .progress { height: 100%; }
  .toggle_btn { float: right; }
</style>
