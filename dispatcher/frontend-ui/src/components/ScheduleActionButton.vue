<!-- Full-featured button to execture schedule/task action by its name

  - request a task
  - unrequest a task
  - cancel a task
  - fire a task
    - by creating it
    - by setting its priority
  - disabled if not signed-in
  - displays a spinner on click
  - calls the API in the background
  - displays result as an AlertFeedback -->

<template>
  <b-button-group v-show="visible" class="action-button">

    <b-dropdown v-show="canRequestTasks"
                v-if="can_select_worker"
                variant="dark" size="sm" right no-flip>
      <template v-slot:button-content>
        <font-awesome-icon icon="server" size="sm" /> {{ selected_worker }}
      </template>

      <b-dropdown-item v-for="worker in all_workers"
                       v-bind:key="worker.name"
                       @click.prevent="change_worker(worker.name);"
                       :variant="worker.status == 'online' ? 'success' : 'secondary'">{{ worker.name }}</b-dropdown-item>
    </b-dropdown>

    <b-button v-show="canRequestTasks"
              v-if="can_request"
              size="sm" variant="info"
              @click.prevent="request_task(cleaned_selected_worker)">
      <font-awesome-icon icon="plus-circle" size="sm" /> Request
    </b-button>
    <b-button v-show="canUnRequestTasks"
              v-if="can_unrequest"
              size="sm" variant="secondary"
              @click.prevent="unrequest_task">
      <font-awesome-icon icon="trash-alt" size="sm" /> Un-request
    </b-button>
    <b-button v-show="canCancelTasks"
              v-if="can_cancel"
              size="sm" variant="danger"
              @click.prevent="cancel_task">
      <font-awesome-icon icon="stop-circle" size="sm" /> Cancel
    </b-button>
    <b-button v-show="canRequestTasks"
              v-if="can_fire"
              size="sm" variant="warning"
              @click.prevent="request_task(cleaned_selected_worker, true)">
      <font-awesome-icon icon="sort-amount-up" size="sm" /> Request
    </b-button>
    <b-button v-show="canRequestTasks"
              v-if="can_fire_existing"
              size="sm" variant="warning"
              @click.prevent="fire_existing_task()">
      <font-awesome-icon icon="sort-amount-up" size="sm" /> Prioritize
    </b-button>
    <b-button v-if="working"
              :disabled="working" size="sm" variant="secondary">
      <font-awesome-icon icon="spinner" size="sm" spin /> {{ working_text}}
    </b-button>
  </b-button-group>
</template>

<script type="text/javascript">
  import Constants from '../constants.js'
  import ZimfarmMixins from '../components/Mixins.js'

  let any_worker_name = "Any";

  export default {
    name: 'ScheduleActionButton',
    mixins: [ZimfarmMixins],
    props: {
      name: String,
    },
    data() {
      return {
        ready: false,
        working_text: null,  // describing text of working action (or null)
        task: null,  // existing task item (from /tasks/ for this schedule (or false)
        requested_task: {},  // existing requested-task _id for this schedule (or false)
        workers: [],  // API-retrieved list of workers
        selected_worker: any_worker_name,  // name of selected worker
      }
    },
    computed: {
      task_id() { return this.task ? this.task._id : this.task; },
      visible() { return (this.ready && (this.canRequestTasks || this.canUnRequestTasks || this.canCancelTasks)); },
      working() { return Boolean(this.working_text); },
      is_running() { return this.task_id === null ? null : Boolean(this.task_id); },
      is_scheduled() { return this.requested_task_id === null ? null : Boolean(this.requested_task_id); },
      can_request() { return !this.working && !this.is_running && !this.is_scheduled; },
      can_fire() { return !this.working && this.can_request; },
      can_fire_existing() { return (!this.working && this.is_scheduled && !this.requested_task.priority); },
      can_cancel() { return !this.working && this.is_running && this.task_id; },
      can_unrequest() { return !this.working && this.is_scheduled; },
      can_select_worker() { return (this.can_request || this.can_fire ) && this.workers.length > 0; },
      should_display_loader() { return this.working; },
      all_workers() { return this.workers.add({name: any_worker_name, status:"offline"}, 0); },
      cleaned_selected_worker() { return this.selected_worker == any_worker_name ? null : this.selected_worker; },
      requested_task_id() { return this.requested_task._id },
    },
    methods: {
      change_worker(worker_name) { this.selected_worker = worker_name; },
      loadData() { // look for req task and task for our schedule
                   // update our IDs based on response
                   // should any fail, don't set ready=true > nothing displayed
        let parent = this;

        parent.requested_task = {};
        parent.queryAPI('get', '/requested-tasks/', {params: {schedule_name: [parent.name]}})
        .then(function (response) {
            if (response.data.meta.count > 0) {
              parent.requested_task = response.data.items[0];
            }

            // once requested-tasks is ran, look for running ones
            parent.queryAPI('get', '/tasks/', {params: {schedule_name: [parent.name], status: Constants.cancelable_statuses}})
              .then(function (response) {
                if (response.data.meta.count > 0) {
                  parent.task = response.data.items[0];
                } else {
                  parent.task = false;  // we have no task ID
                }
                // now that we receive all info, consider ourselves ready
                parent.ready = true;
              }).catch(function() {
                parent.ready = false;
              });
          })
          .catch(function() {
            parent.ready = false;
          });

        parent.queryAPI('get', '/workers/')
        .then(function (response) {
            parent.workers = response.data.items;
          });
      },
      request_task(worker_name, priority) {

        let parent = this;
        parent.working_text = "Requesting task…";

        let params = {schedule_names: [parent.name]};
        if (priority)
          params.priority = Constants.DEFAULT_FIRE_PRIORITY;
        if (worker_name)
          params.worker =  worker_name;
        parent.queryAPI('post', '/requested-tasks/', params)
          .then(function (response) {
            parent.requested_task = {_id: response.data.requested[0], priority: priority || 0};
            let msg = "Schedule <em>" + parent.name + "</em> has been requested as <code>" + Constants.short_id(parent.requested_task_id) + "</code>.";

            parent.alertSuccess("Scheduled!", msg);
          })
          .catch(function (error) {
            parent.alertError(Constants.standardHTTPError(error.response));
          })
          .then(function () {
            parent.working_text = null;
            parent.loadData();
          });
      },
      fire_existing_task() {  // increase priority of existing request
        let parent = this;
        if (!parent.requested_task_id)
          return;

        parent.working_text = "Firing it up…";
        parent.queryAPI('patch', '/requested-tasks/' + parent.requested_task_id, {priority: Constants.DEFAULT_FIRE_PRIORITY})
        .then(function () {
          let msg = "Added priority to request <code>" + Constants.short_id(parent.requested_task_id) + "</code>.";

          parent.alertSuccess("Prioritized!", msg);
        })
        .catch(function (error) {
          parent.alertError(Constants.standardHTTPError(error.response));
        })
        .then(function () {
          parent.working_text = null;
          parent.loadData();
        });
      },
      cancel_task() {
        let parent = this;
        parent.working_text = "Canceling task…";

        parent.queryAPI('post', '/tasks/' + parent.task_id + '/cancel')
          .then(function () {
            let msg = "Requested Task <code>" + Constants.short_id(parent.task_id) + "</code> has been marked for cancelation.";
            parent.task = null;

            parent.alertSuccess("Canceling!", msg);
          })
          .catch(function (error) {
            parent.alertError(Constants.standardHTTPError(error.response));
          })
          .then(function () {
            parent.working_text = null;
            parent.loadData();
          });
      },
      unrequest_task() {
        let parent = this;
        parent.working_text = "Un-requesting task…";

        parent.queryAPI('delete', '/requested-tasks/' + parent.requested_task_id)
          .then(function () {
            let msg = "Requested Task <code>" + Constants.short_id(parent.requested_task_id) + "</code> has been removed.";
            parent.requested_task = {};

            parent.alertSuccess("Un-scheduled!", msg);
          })
          .catch(function (error) {
            parent.alertError(Constants.standardHTTPError(error.response));
          })
          .then(function () {
            parent.working_text = null;
            parent.loadData();
          });
      },
    },
    mounted() {
      this.loadData();
    },
  }
</script>

<style type="text/css" scoped>
  .action-button {
    margin-left: auto;
    margin-right: 1rem;
  }
</style>
