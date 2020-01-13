<!-- Schedule detail view
  - listing all info
  - fire schedule button -->

<template>
  <div class="container">
    <div class="row"><ScheduleActionButton :name="schedule_name" /></div>
    <div class="row"><div class="col"><h2><code>{{ schedule_name }}</code></h2></div></div>

    <div v-if="!error && ready">
      <ul class="nav nav-tabs">
        <li class="nav-item" :class="{ active: selectedTab == 'details'}">
          <router-link class="nav-link"
                       active-class="dummy"
                       :class="{ active: selectedTab == 'details'}"
                       :to="{name: 'schedule-detail', params: {schedule_name: schedule_name}}">
            Info
          </router-link>
        </li>
        <li class="nav-item" :class="{ active: selectedTab == 'config'}">
          <router-link class="nav-link schedule-config-tab"
                       active-class="dummy"
                       :class="{ active: selectedTab == 'config'}"
                       :to="{name: 'schedule-detail-tab', params: {schedule_name: schedule_name, selectedTab: 'config'}}">
            <span>Config</span>
          </router-link>
        </li>
        <li v-show="canUpdateSchedules" class="nav-item" :class="{ active: selectedTab == 'edit'}">
          <router-link class="nav-link"
                       active-class="dummy"
                       :class="{ active: selectedTab == 'edit'}"
                       :to="{name: 'schedule-detail-tab', params: {schedule_name: schedule_name, selectedTab: 'edit'}}">
            Edit
          </router-link>
        </li>
        <li v-show="canCreateSchedules" class="nav-item" :class="{ active: selectedTab == 'clone'}">
          <router-link class="nav-link text-info"
                       active-class="dummy"
                       :class="{ active: selectedTab == 'clone'}"
                       :to="{name: 'schedule-detail-tab', params: {schedule_name: schedule_name, selectedTab: 'clone'}}">
            Clone
          </router-link>
        </li>
        <li v-show="canDeleteSchedules" class="nav-item" :class="{ active: selectedTab == 'delete'}">
          <router-link class="nav-link text-danger schedule-delete-tab"
                       active-class="dummy"
                       :class="{ active: selectedTab == 'delete'}"
                       :to="{name: 'schedule-detail-tab', params: {schedule_name: schedule_name, selectedTab: 'delete'}}">
            <span>Delete</span>
          </router-link>
        </li>
      </ul>

      <div v-if="selectedTab == 'details'" class="tab-content">
        <table class="table table-responsive-md table-striped table-in-tab">
          <tr><th>API</th><td><a target="_blank" :href="webapi_url + '/schedules/' + schedule_name">document <font-awesome-icon icon="external-link-alt" size="sm" /></a></td></tr>
          <tr><th>Category</th><td>{{ schedule.category }}</td></tr>
          <tr><th>Language</th><td>{{ schedule.language.name_en }} (<code>{{ schedule.language.code }}</code>)</td></tr>
          <tr><th>Enabled</th><td><code>{{ schedule.enabled }}</code></td></tr>
          <tr><th>Periodicity</th><td><code>{{ schedule.periodicity }}</code></td></tr>
          <tr v-if="schedule.tags.length">
            <th>Tags</th>
            <td>
              <span v-for="tag in schedule.tags" v-bind:key="tag" class="badge badge-dark mr-2">{{ tag }}</span>
            </td>
          </tr>
          <tr>
            <th>Last run</th>
            <td v-if="last_run">
              <code>{{ last_run.status }}</code>,
              <TaskLink :_id="last_run._id" :updated_at="last_run.updated_at" />
            </td>
            <td v-else><code>none</code> 🙁</td>
          </tr>
          <tr v-if="!canRequestTasks">
            <th>Requested</th>
            <td v-if="requested === null"><font-awesome-icon icon="spinner" spin /></td>
            <td v-else-if="requested"><code>{{ requested_id | short_id }}</code>, {{ requested.timestamp.requested | from_now }} <b-badge pill variant="warning" v-if="requested.priority"><font-awesome-icon icon="fire" size="sm" /> {{ requested.priority }}</b-badge></td>
            <td v-else><code>no</code></td>
          </tr>
          <tr v-if="schedule.duration">
            <th>Duration</th>
            <td>
              <span v-if="duration_dict.single">
                {{ duration_dict.value | duration }} (<code>{{ duration_dict.worker }}</code> on {{ duration_dict.on | format_dt }})</span>
              <span v-else>
                between {{ duration_dict.min_value | duration }} (<code
                 v-for="worker in duration_dict.min_workers"
                 :key="worker.worker"><TaskLink
                  :_id="worker.task"
                  :updated_at="worker.on"
                  :text="worker.worker" /></code>) and {{ duration_dict.max_value | duration }} (<code
                    v-for="worker in duration_dict.max_workers"
                    :key="worker.worker"><TaskLink
                      :_id="worker.task"
                      :updated_at="worker.on"
                      :text="worker.worker" /></code>)
              </span>
            </td>
          </tr>
          <tr>
            <th>History</th>
            <td v-if="history_runs">
              <table class="table table-sm table-striped">
                <tbody>
                <tr v-for="run in history_runs" :key="run._id">
                  <td><code :class="statusClass(run.status)">{{ run.status }}</code></td>
                  <td><TaskLink :_id="run._id" :updated_at="run.updated_at" /></td>
                </tr>
              </tbody>
              </table>
            </td>
            <td v-else><code>none</code> 🙁</td>
          </tr>
        </table>
      </div>

      <div v-if="selectedTab == 'config'" class="tab-content">
        <table class="table table-responsive-md table-striped table-in-tab">
          <tr><th>Offliner</th><td><code>{{ offliner }}</code></td></tr>
          <tr><th>Warehouse path</th><td><code>{{ warehouse_path }}</code></td></tr>
          <tr><th>Image</th><td><a target="_blank" :href="'https://hub.docker.com/r/' + config.image.name"><code>{{ image_human }}</code></a></td></tr>
          <tr>
            <th>Resources</th>
            <td>
              <ResourceBadge kind="cpu" :value="config.resources.cpu" />
              <ResourceBadge kind="memory" :value="config.resources.memory" />
              <ResourceBadge kind="disk" :value="config.resources.disk" />
            </td>
          </tr>
          <tr><th>Config</th><td><FlagsList :flags="config.flags" /></td></tr>
          <tr><th>Command <button class="btn btn-light btn-sm" @click.prevent="copyCommand"><font-awesome-icon icon="copy" size="sm" /> Copy</button></th><td><code class="command">{{ command }}</code></td></tr>
        </table>
      </div>
    </div>

    <div v-if="selectedTab == 'edit' && canUpdateSchedules" class="tab-content edit-tab">
      <ScheduleEditor :schedule_name="schedule_name"></ScheduleEditor>
    </div>

    <div v-if="selectedTab == 'clone' && canCreateSchedules" class="tab-content edit-tab">
      <CloneSchedule :from="schedule_name" />
    </div>

    <div v-if="selectedTab == 'delete' && canDeleteSchedules" class="tab-content edit-tab">
      <DeleteItem kind="schedule" :name="schedule_name" />
    </div>

    <ErrorMessage :message="error" v-if="error" />
  </div>
</template>

<script>
  import Constants from '../constants.js'
  import ZimfarmMixins from '../components/Mixins.js'
  import ErrorMessage from '../components/ErrorMessage.vue'
  import ScheduleActionButton from '../components/ScheduleActionButton.vue'
  import ResourceBadge from '../components/ResourceBadge.vue'
  import ScheduleEditor from '../components/ScheduleEditor.vue'
  import DeleteItem from '../components/DeleteItem.vue'
  import CloneSchedule from '../components/CloneSchedule.vue'
  import FlagsList from '../components/FlagsList.vue'
  import TaskLink from '../components/TaskLink.vue'

  export default {
    name: 'ScheduleView',
    mixins: [ZimfarmMixins],
    components: {ScheduleActionButton, ErrorMessage, ResourceBadge,
                 ScheduleEditor, DeleteItem, CloneSchedule, FlagsList, TaskLink},
    props: {
      schedule_name: String,  // the schedule name/ID
      selectedTab: {  // currently selected tab: details, container, debug
        type: String,
        default: 'details'
      },
    },
    data() {
      return {
        ready: false,  // whether we are ready to display
        error: null,  // API generated error message
        requested: null,  // task item from API if this is in todo
        history_runs: [],
      };
    },
    computed: {
      webapi_url() { return Constants.zimfarm_webapi; },
      schedule() { return this.$store.getters.schedule || null; },
      name() { return this.schedule.name },
      language_name() { return this.schedule.language.name_en || null; },
      last_run() { return this.schedule.most_recent_task; },
      config() { return this.schedule.config; },
      offliner() { return this.config.task_name; },
      image_human() { return Constants.image_human(this.config); },
      warehouse_path() { return this.config.warehouse_path; },
      command() { return Constants.build_docker_command(this.name, this.config); },
      trimmed_command() { return Constants.trim_command(this.command); },
      requested_id() { return (this.requested) ? this.requested._id : null; },
      duration_dict() { return Constants.schedule_durations_dict(this.schedule.duration); }
    },
    methods: {
      filesize(value) { return Constants.filesize(parseInt(value)); },
      copyCommand() {
        let parent = this;
        this.$copyText(this.command).then(function () {
            parent.alertInfo("Command copied to Clipboard!");
          }, function () {
            parent.alertWarning("Unable to copy command to clipboard 😞. ",
                                "Please copy it manually.");
          });
      },
      setReady() { this.ready = true; },
      setError(error) { this.error = error; },
    },
    mounted() {
      let parent = this;

      // redirect to details if tryng to access Edit tab without permission
      if (this.selectedTab == 'edit' && !this.canUpdateSchedules) {
        parent.redirectTo('schedule-detail', {schedule_name: this.schedule_name});
      }

      parent.$root.$emit('load-schedule', this.schedule_name, false, this.setReady, this.setError);
      parent.requested = null;
      parent.queryAPI('get', '/requested-tasks/', {params: {schedule_name: parent.schedule_name}})
        .then(function (response) {
            if (response.data.meta.count > 0) {
              parent.requested = response.data.items[0];
            } else {
              parent.requested = false;
            }
        })
        .catch(function () {
          parent.requested = false;
        })

      parent.history_runs = [];
      parent.queryAPI('get', '/tasks/', {params: {schedule_name: parent.schedule_name}})
        .then(function (response) {
            parent.history_runs = response.data.items;
        })
        .catch(function () {
        })
    },
  }
</script>


<style type="text/css" scoped>
  .edit-tab {
    padding: 1rem;
  }

  @media (max-width: 500px) {
    .schedule-config-tab span, .schedule-delete-tab span { display: none; }
    .schedule-config-tab:after { content: "Conf"; }
    .schedule-delete-tab:after { content: "Del"; }
  }
</style>
