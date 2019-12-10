<!-- Schedule detail view
  - listing all info
  - fire schedule button -->

<template>
  <div class="container">
    <ScheduleActionButton :name="schedule_name" />
    <h2><code>{{ schedule_name }}</code></h2>

    <div v-if="!error && schedule">
      <ul class="nav nav-tabs">
        <li class="nav-item" :class="{ active: selectedTab == 'details'}">
          <router-link class="nav-link"
                       active-class="dummy"
                       :class="{ active: selectedTab == 'details'}"
                       :to="{name: 'schedule-detail', params: {schedule_name: schedule_name}}">
            Schedule
          </router-link>
        </li>
        <li class="nav-item" :class="{ active: selectedTab == 'config'}">
          <router-link class="nav-link"
                       active-class="dummy"
                       :class="{ active: selectedTab == 'config'}"
                       :to="{name: 'schedule-detail-tab', params: {schedule_name: schedule_name, selectedTab: 'config'}}">
            Config
          </router-link>
        </li>
      </ul>

      <div v-if="selectedTab == 'details'" class="tab-content">
        <table class="table table-responsive-sm table-striped table-in-tab">
          <tr><th>Category</th><td>{{ schedule.category }}</td></tr>
          <tr><th>Language</th><td>{{ schedule.language.name_en }} (<code>{{ schedule.language.code }}</code>)</td></tr>
          <tr><th>Enabled</th><td><code>{{ schedule.enabled }}</code></td></tr>
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
              <router-link :to="{name: 'task-detail', params: {_id: last_run._id}}">{{ last_run.on }}</router-link>
            </td>
            <td v-else><code>none</code> 🙁</td>
          </tr>
          <tr>
            <th>Requested</th>
            <td v-if="requested === null"><font-awesome-icon icon="spinner" spin /></td>
            <td v-else-if="requested"><router-link :to="{ name: 'task-detail', params: {_id: requested_id}}"><code>{{ requested_id }}</code></router-link>, {{ requested_since }}</td>
            <td v-else><code>no</code></td>
          </tr>
        </table>
      </div>

      <div v-if="selectedTab == 'config'" class="tab-content">
        <table class="table table-responsive-sm table-striped table-in-tab">
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
          <tr><th>Command <button class="btn btn-light btn-sm" @click.prevent="copyCommand"><font-awesome-icon icon="copy" size="sm" /> Copy</button></th><td><pre>{{ trimmed_command }}</pre></td></tr>
        </table>
      </div>
    </div>
    <ErrorMessage :message="error" v-if="error" />
  </div>
</template>

<script>
  import moment from 'moment';

  import Constants from '../constants.js'
  import ZimfarmMixins from '../components/Mixins.js'
  import ErrorMessage from '../components/ErrorMessage.vue'
  import ScheduleActionButton from '../components/ScheduleActionButton.vue'
  import ResourceBadge from '../components/ResourceBadge.vue'

  export default {
    name: 'ScheduleView',
    mixins: [ZimfarmMixins],
    components: {ScheduleActionButton, ErrorMessage, ResourceBadge},
    props: {
      schedule_name: String,  // the schedule name/ID
      selectedTab: {  // currently selected tab: details, container, debug
        type: String,
        default: 'details'
      },
    },
    data() {
      return {
        error: null,  // API generated error message
        schedule: null,  // schedule document returned by API
        requested: null,
      };
    },
    computed: {
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
      requested_time() { return this.format_dt(this.requested.timestamp.requested); },
      requested_since() { return Constants.from_now(this.requested_time); }
    },
    methods: {
      copyCommand() {
        let parent = this;
        this.$copyText(this.command).then(function () {
            parent.$root.$emit('feedback-message', 'info', "Command copied to Clipboard!");
          }, function () {
            parent.$root.$emit('feedback-message',
                         'warning',
                         "Unable to copy command to clipboard 😞. " +
                         "Please copy it manually.");
          });
      },
    },
    mounted() {
      let parent = this;

      parent.toggleLoader("fetching schedule…");
      parent.$root.axios.get('/schedules/' + this.schedule_name)
        .then(function (response) {
            parent.error = null;

            parent.schedule = response.data;
            if (parent.schedule.most_recent_task) {
              parent.schedule.most_recent_task.on = moment(parent.schedule.most_recent_task.updated_at).fromNow();
            }
        })
        .catch(function (error) {
          parent.error = Constants.standardHTTPError(error.response);
        })
        .then(function () {
            parent.toggleLoader(false);
        });

      parent.$root.axios.get('/requested-tasks/')
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
    },
  }
</script>
