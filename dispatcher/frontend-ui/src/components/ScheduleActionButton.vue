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
  <b-button-group v-show="visible">
    <b-button v-show="canRequestTasks"
              v-if="can_request && !workers.length"
              size="sm" variant="info"
              @click.prevent="request_task(null)">
      <font-awesome-icon icon="calendar-alt" size="sm" /> Request
    </b-button>
    <b-dropdown v-show="canRequestTasks"
                v-if="can_request && workers.length"
                no-flip split size="sm" variant="info"
                @click.prevent="request_task(null)">
      <template v-slot:button-content><font-awesome-icon icon="calendar-alt" size="sm" /> Request</template>
      <b-dropdown-item v-for="worker in workers"
                       v-bind:key="worker.name"
                       @click.prevent="request_task(worker.name);"
                       :variant="worker.status == 'online' ? 'success' : 'secondary'">{{ worker.name }}</b-dropdown-item>
    </b-dropdown>
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
              @click.prevent="fire_task">
      <font-awesome-icon icon="fire" size="sm" /> Fire
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
        requested_task_id: null,  // existing requested-task _id for this schedule (or false)
        workers: [],  // API-retrieved list of workers
      }
    },
    computed: {
      task_id() { return this.task ? this.task._id : this.task; },
      visible() { return (this.ready && (this.canRequestTasks || this.canUnRequestTasks || this.canCancelTasks)); },
      working() { return Boolean(this.working_text); },
      is_running() { return this.task_id === null ? null : Boolean(this.task_id); },
      is_scheduled() { return this.requested_task_id === null ? null : Boolean(this.requested_task_id); },
      can_request() { return !this.working && !this.is_running && !this.is_scheduled; },
      can_fire() { return !this.working && (this.can_request || this.is_scheduled) },
      can_cancel() { return !this.working && this.is_running && this.task_id; },
      can_unrequest() { return !this.working && this.is_scheduled; },
      should_display_loader() { return this.working; },
    },
    methods: {
      loadData() { // look for req task and task for our schedule
                   // update our IDs based on response
                   // should any fail, don't set ready=true > nothing displayed
        let parent = this;

        parent.$root.axios.get('/requested-tasks/', {params: {schedule_name: [parent.name]}})
        .then(function (response) {
            if (response.data.meta.count > 0) {
              parent.requested_task_id = response.data.items[0]._id;
            } else {
              parent.requested_task_id = false;  // we have no req ID
            }

            // once requested-tasks is ran, look for running ones
            parent.$root.axios.get('/tasks/', {params: {schedule_name: [parent.name], status: Constants.running_statuses}})
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

        parent.$root.axios.get('/workers/')
        .then(function (response) {
            parent.workers = response.data.items;
          });
      },
      request_task(worker_name) {
        let parent = this;
        parent.working_text = "Requesting task…";

        let params = {schedule_names: [parent.name]};
        if (worker_name)
          params.worker =  worker_name;
        parent.$root.axios.post('/requested-tasks/', params)
          .then(function (response) {
            parent.requested_task_id = response.data.requested[0];
            let msg = "Schedule <em>" + parent.name + "</em> has been requested as <code>" + Constants.short_id(parent.requested_task_id) + "</code>.";

            parent.$root.$emit('feedback-message', 'success', "<strong>Scheduled!</strong><br />" + msg);
          })
          .catch(function (error) {
            parent.$root.$emit('feedback-message',
                               'danger',
                               "<strong>Not Scheduled!</strong><br />" + Constants.standardHTTPError(error.response));
          })
          .then(function () {
            parent.working_text = null;
            parent.loadData();
          });
      },
      fire_task() {
        let parent = this;
        parent.working_text = "Firing it up…";

        if (parent.requested_task_id) {  // increase priority of existing request
          parent.$root.axios.patch('/requested-tasks/' + parent.requested_task_id, {priority: Constants.DEFAULT_FIRE_PRIORITY})
          .then(function () {
            let msg = "Added priority to request <code>" + Constants.short_id(parent.requested_task_id) + "</code>.";

            parent.$root.$emit('feedback-message', 'success', "<strong>Fired!</strong><br />" + msg);
          })
          .catch(function (error) {
            parent.$root.$emit('feedback-message',
                               'danger',
                               "<strong>Not Fired!</strong><br />" + Constants.standardHTTPError(error.response));
          })
          .then(function () {
            parent.working_text = null;
            parent.loadData();
          });

        } else {  // create a request with higher priority
          parent.$root.axios.post('/requested-tasks/', {schedule_names: [parent.name], priority: Constants.DEFAULT_FIRE_PRIORITY})
          .then(function (response) {
            parent.requested_task_id = response.data.requested[0];
            let msg = "Recipe <em>" + parent.name + "</em> has been requested with priority as <code>" + Constants.short_id(parent.requested_task_id) + "</code>.";

            parent.$root.$emit('feedback-message', 'success', "<strong>Fired!</strong><br />" + msg);
          })
          .catch(function (error) {
            parent.$root.$emit('feedback-message',
                               'danger',
                               "<strong>Not Scheduled!</strong><br />" + Constants.standardHTTPError(error.response));
          })
          .then(function () {
            parent.working_text = null;
            parent.loadData();
          });
        }
      },
      cancel_task() {
        let parent = this;
        parent.working_text = "Canceling task…";

        parent.$root.axios.post('/tasks/' + parent.task_id + '/cancel')
          .then(function () {
            let msg = "Requested Task <code>" + Constants.short_id(parent.task_id) + "</code> has been marked for cancelation.";
            parent.task = null;

            parent.$root.$emit('feedback-message', 'success', "<strong>Canceling!</strong><br />" + msg);
          })
          .catch(function (error) {
            parent.$root.$emit('feedback-message',
                               'danger',
                               "<strong>Not Canceling!</strong><br />" + Constants.standardHTTPError(error.response));
          })
          .then(function () {
            parent.working_text = null;
            parent.loadData();
          });
      },
      unrequest_task() {
        let parent = this;
        parent.working_text = "Un-requesting task…";

        parent.$root.axios.delete('/requested-tasks/' + parent.requested_task_id)
          .then(function () {
            let msg = "Requested Task <code>" + Constants.short_id(parent.requested_task_id) + "</code> has been removed.";
            parent.requested_task_id = null;

            parent.$root.$emit('feedback-message', 'success', "<strong>Un-scheduled!</strong><br />" + msg);
          })
          .catch(function (error) {
            parent.$root.$emit('feedback-message',
                               'danger',
                               "<strong>Not Un-scheduled!</strong><br />" + Constants.standardHTTPError(error.response));
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
  div { float: right; }
</style>
