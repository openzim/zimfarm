<!-- Schedule detail view
  - listing all info
  - fire schedule button -->

<template>
  <div class="container">


    <BackButton class="mb-2" />
    <h1><code>{{ schedule_name }}</code> <FireScheduleButton :name="schedule_name" /></h1>
    <div v-if="!error">
      <ul class="nav nav-tabs">
        <li class="nav-item"><a href="#" class="nav-link" :class="{ active: selectedTab == 'details'}" @click.prevent="selectedTab='details'">Schedule</a></li>
        <li class="nav-item"><a href="#" class="nav-link" :class="{ active: selectedTab == 'flags'}" @click.prevent="selectedTab='flags'">Flags</a></li>
      </ul>

      <div v-if=" selectedTab == 'details'" class="details">
        <table class="table table-responsive-sm table-striped">
          <tr><th>Category</th><td>{{ schedule.category }}</td></tr>
          <tr><th>Language</th><td>{{ schedule.language.name_en }} (<code>{{ schedule.language.code }}</code>)</td></tr>
          <tr><th>Enabled</th><td><code>{{ schedule.enabled }}</code></td></tr>
          <tr v-if="schedule.tags.length">
            <th>Tags</th>
            <td>
              <span v-for="tag in schedule.tags" v-bind:key="tag" class="badge badge-dark mr-2">{{ tag }}</span>
            </td>
          </tr>
          <tr v-if="last_run">
            <th>Last run</th>
            <td><code>{{ last_run.status }}</code>,
                <router-link :to="{name: 'task-detail', params: {_id: last_run._id}}">{{ last_run.on }}</router-link>
            </td>
          </tr>
          <tr>
            <th>Resources</th>
            <td>
              <span class="badge badge-light mr-2" v-tooltip="'CPU'"><font-awesome-icon icon="microchip" /> {{ cpu_human }}</span>
              <span class="badge badge-light mr-2" v-tooltip="'Memory'"><font-awesome-icon icon="memory" /> {{ memory_human }}</span>
              <span class="badge badge-light mr-2" v-tooltip="'Disk'"><font-awesome-icon icon="hdd" /> {{ disk_human }}</span>
            </td>
          </tr>
        </table>
      </div>

      <div v-if=" selectedTab == 'flags'" class="details">
        <h3>Command</h3>
        <code>{{ command }}</code>
      </div>
    </div>
    <ErrorMessage :message="error" v-if="error" />
  </div>
</template>

<script>
  import moment from 'moment';
  import filesize from 'filesize';

  import Constants from '../constants.js'
  import ZimfarmMixins from '../components/Mixins.js'
  import BackButton from '../components/BackButton.vue'
  import ErrorMessage from '../components/ErrorMessage.vue'
  import FireScheduleButton from '../components/FireScheduleButton.vue'

  export default {
    name: 'ScheduleView',
    mixins: [ZimfarmMixins],
    components: {BackButton, FireScheduleButton, ErrorMessage},
    props: {
      schedule_name: String,  // the schedule name/ID
    },
    data() {
      return {
        error: null,  // API generated error message
        schedule: null,  // schedule document returned by API
        selectedTab: 'details',  // currently selected tab: details, container, debug
      };
    },
    computed: {
      name() { return this.schedule.name },
      language_name() { return this.schedule.language.name_en || null; },
      last_run() { return this.schedule.most_recent_task; },
      config() { return this.schedule.config; },
      offliner() { return this.config.task_name; },
      cpu_human() { return this.config.resources.cpu; },
      memory_human() { return filesize(this.config.resources.memory); },
      disk_human() { return filesize(this.config.resources.disk); },
      image_human() { return this.config.image.name + ":" + this.config.image.tag; },
      command() {  // copy of what docker command should be (actually computer on worker)
        let mounts = ["-v ", "/my-path:" + this.config.mount_point + ":rw"];
        let mem_params = ["--memory-swappiness", "0", "--memory", this.config.resources.memory];
        let cpu_params = ["--cpu-shares", this.config.resources.cpu * Constants.DEFAULT_CPU_SHARE];
        let docker_base = ["docker", "run"].concat(mounts) .concat(["--name", this.offliner + "_" + this.name, "--detach"]).concat(cpu_params).concat(mem_params);
        let scraper_command = this.config.str_command;
        let args = docker_base.concat([this.image_human]).concat([scraper_command]);
        return args.join(" ");
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
