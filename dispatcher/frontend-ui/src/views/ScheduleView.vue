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
        <li v-show="canEditSchedule" class="nav-item" :class="{ active: selectedTab == 'edit'}">
          <router-link class="nav-link"
                       active-class="dummy"
                       :class="{ active: selectedTab == 'edit'}"
                       :to="{name: 'schedule-detail-tab', params: {schedule_name: schedule_name, selectedTab: 'edit'}}">
            Edit
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

    <div v-if="selectedTab == 'edit' && canEditSchedule" class="tab-content edit-tab">
      <b-form @submit.prevent="commit_form" @reset.prevent="reset_form">

        <b-row class="mb-3">
          <b-col class="text-right">
            <b-button
              :disabled="!payload"
              type="submit"
              :variant="payload ? 'primary' : 'secondary'">Update Offliner details</b-button>
            <b-button
              type="reset"
              :disabled="!payload"
              :variant="payload ? 'dark' : 'secondary'"
              class="ml-2">Reset</b-button>
          </b-col>
        </b-row>

        <b-row>
          <b-col>
            <b-form-group label="Recipe Name:"
                          label-for="es_name"
                          description="Recipe's identifier.">
              <b-form-input v-model="edit_name"
                            id="es_name"
                            type="text"
                            required
                            placeholder="wikipedia_fr_all"
                            size="sm"></b-form-input>
            </b-form-group>
          </b-col>
          <b-col>
            <b-form-group label="Category:" label-for="es_category">
              <b-form-select id="es_category"
                             v-model="edit_category"
                             :options="categoriesOptions"
                             size="sm"></b-form-select>
            </b-form-group>
          </b-col>
          <b-col>
            <b-form-group label="Language:" label-for="es_language" description="Use API if wanted language not present.">
              <b-form-select id="es_language"
                             v-model="edit_language_code"
                             :options="languagesOptions"
                             size="sm"></b-form-select>
            </b-form-group>
          </b-col>
        </b-row>

        <b-row>
          <b-col>
            <b-form-group label="Status:" label-for="es_enable" description="Disabled recipe can't be scheduled.">
              <SwitchButton v-model="edit_enabled">{{ edit_enabled|yes_no("Enabled", "Disabled") }}</SwitchButton>
            </b-form-group>
          </b-col>
          <b-col>
            <b-form-group label="Warehouse Path:" label-for="es_warehouse_path" description="Where to upload files. Usually matches category.">
              <b-form-select id="es_warehouse_path"
                              v-model="edit_warehouse_path"
                              :options="warehouse_pathsOptions"
                              required
                              placeholder="Warehouse Path"
                              size="sm"></b-form-select>
            </b-form-group>
          </b-col>
          <b-col>
            <b-form-group label="Tags:" label-for="es_tags" description="Recipe tags, not ZIM tags. Use API to create others.">
              <multiselect v-model="edit_tags"
                     :options="tags"
                     :multiple="true"
                     :clear-on-select="true"
                     :preserve-search="true"
                     :searchable="true"
                     :closeOnSelect="true"
                     placeholder="Tags"
                     size="sm"></multiselect>
            </b-form-group>
          </b-col>
        </b-row>

      <hr />

        <b-row>
          <b-col>
            <b-form-group label="Offliner:"
                          label-for="es_offliner"
                          description="The kind of task to be run">
              <b-form-select id="es_category"
                             v-model="edit_task_name"
                             :options="offlinersOptions"
                             size="sm"></b-form-select>
            </b-form-group>
          </b-col>
          <b-col>
            <b-form-group label="Image Name:" label-for="es_image" description="Just the image name (repo/name)">
              <b-form-input v-model="edit_image_name"
                            id="es_image"
                            type="text"
                            required
                            placeholder="openzim/mwoffliner"
                            size="sm"></b-form-input>
            </b-form-group>
          </b-col>
          <b-col>
            <b-form-group label="Image Tag:" label-for="es_imagetag" description="Just the tag name. `latest` usually.">
              <b-form-input v-model="edit_image_tag"
                            id="es_imagetag"
                            type="text"
                            required
                            placeholder="latest"
                            size="sm"></b-form-input>
            </b-form-group>
          </b-col>
        </b-row>

        <b-row>
          <b-col>
            <b-form-group label="CPU:"
                          label-for="es_cpu"
                          description="Number of CPU shares to use">
              <b-form-input v-model="edit_cpu"
                            id="es_cpu"
                            type="number"
                            min="1"
                            max="100"
                            required
                            placeholder="3"
                            size="sm"></b-form-input>
            </b-form-group>
          </b-col>
          <b-col>
            <b-form-group label="Memory:"
                          label-for="es_memory"
                          description="Required memory. Use API for custom value.">
              <b-form-select id="es_memory"
                             v-model="edit_memory"
                             :options="memoryOptions"
                             size="sm"></b-form-select>
            </b-form-group>
          </b-col>
          <b-col>
            <b-form-group label="Disk:"
                          label-for="es_disk"
                          description="Required disk space. Use API for custom value.">
              <b-form-select id="es_disk"
                             v-model="edit_disk"
                             :options="diskOptions"
                             size="sm"></b-form-select>
            </b-form-group>
          </b-col>
        </b-row>

        <hr />

        <b-row><b-col><h2><code>{{ edit_task_name}}</code> command flags</h2></b-col></b-row>

        <table class="table table-striped table-hover table-sm table-responsive-sm">
          <tbody>
          <tr v-for="field in edit_flags_fields" :key="field.data_key">
            <th>{{ field.label }}<sup v-if="field.required">&nbsp;<font-awesome-icon icon="asterisk" color="red" size="xs" /></sup></th>
            <td>
              <multiselect v-if="field.component == 'multiselect'"
                v-model="edit_flags[field.data_key]"
                :options="field.options"
                :multiple="true"
                :clear-on-select="true"
                :preserve-search="true"
                :searchable="true"
                :closeOnSelect="true"
                :placeholder="field.placeholder"
                size="sm"></multiselect>
              <component v-else
               :is="field.component"
               :name="'es_flags_' + field.data_key"
               :required="field.required"
               :placeholder="field.placeholder"
               v-model="edit_flags[field.data_key]"
               :style="{backgroundColor: field.bind_color ? edit_flags[field.data_key]: ''}"
               size="sm"
               :type="field.component_type">
                 <option v-for="option in field.options" :key="option.value" :value="option.value">{{ option.text }}</option>
               </component>
              <b-form-text>{{ field.description }}</b-form-text>
            </td>
          </tr>
        </tbody>
        </table>

      <b-row>
          <b-col>
            <b-button
              :disabled="!payload"
              type="submit"
              :variant="payload ? 'primary' : 'secondary'">Update Offliner details</b-button>
            <b-button
              type="reset"
              :disabled="!payload"
              :variant="payload ? 'dark' : 'secondary'"
              class="ml-2">Reset</b-button>
          </b-col>
        </b-row>

      </b-form>
    </div>

    <div v-if="selectedTab == 'edit' && !canEditSchedule" class="tab-content edit-tab"><p>Can't edit!</p></div>

    <ErrorMessage :message="error" v-if="error" />
  </div>
</template>

<script>
  import diff from 'deep-diff'
  import moment from 'moment';

  import Constants from '../constants.js'
  import ZimfarmMixins from '../components/Mixins.js'
  import ErrorMessage from '../components/ErrorMessage.vue'
  import ScheduleActionButton from '../components/ScheduleActionButton.vue'
  import ResourceBadge from '../components/ResourceBadge.vue'
  import SwitchButton from '../components/SwitchButton.vue'

  export default {
    name: 'ScheduleView',
    mixins: [ZimfarmMixins],
    components: {ScheduleActionButton, ErrorMessage, ResourceBadge, SwitchButton},
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
        requested: null,  // task item from API if this is in todo
        edit_schedule: null, // data holder for edition
        languages: [],  // list of languages for editing
        tags: [],  // list of tags for editing

        // edit fields
        edit_name: null,
        edit_schedule_name: null,
        edit_category: null,
        edit_language_code: null,
        edit_enabled: null,
        edit_warehouse_path: null,
        edit_tags: null,

        edit_task_name: null,
        edit_image_name: null,
        edit_image_tag: null,
        edit_cpu: null,
        edit_memory: null,
        edit_disk: null,
        edit_flags: {},

        flags_definition: [],  // schema definition from API for task_name
      };
    },
    computed: {
      edit_flags_fields() {
        let fields = [];
        for (var i=0;i<this.flags_definition.length;i++) {
          let field = this.flags_definition[i];
          let component = "b-form-input";
          let options = null;
          let component_type = null;
          let bind_color = null;

          if (field.type == "hex-color") {
            bind_color = true;
          }

          if (field.type == "url") {
            component = "b-form-input";
            component_type = "url";
          }

          if (field.type == "email") {
            component = "b-form-input";
            component_type = "email";
          }

          if (field.type == "integer") {
            component = "b-form-input";
            component_type = "number";
          }

          if (field.type == "float") {
            component = "b-form-input";
            component_type = "number";
          }

          if (field.type == "list-of-string-enum") {
            component = "multiselect";
            options = field.choices;
          }

          if (field.type == "boolean") {
            component = "b-form-select";
            options = [{text: "True", value: true}, {text: "Not set", value: undefined}];
          }

          if (field.type == "string-enum") {
            component = "b-form-select";
            options = field.choices.map(function (option) { return {text: option, value: option}; });
          }

          if (field.type == "text") {
            component = "b-form-input";
            component_type = "text";
          }

          fields.push({
            label: field.label || field.data_key,
            data_key: field.data_key,
            required: field.required,
            description: field.description,
            placeholder: "Not set",  //field.placeholder,

            component: component,
            component_type: component_type,
            options: options,
            bind_color: bind_color,
          });

        }
        return fields;
      },
      flags_payload() {
        let changes = diff(this.schedule.config.flags, this.edit_flags);
        if (!changes)
          return false;
        changes = changes.filter(function (change) {
          if (change.kind == "N" && change.rhs == "") {  // empty change
            return false;
          }
          return true;
        });
        if (!changes.length)
          return false;

        let payload = Constants.duplicate(this.edit_flags);
        if (Object.keys(payload).length == 0)
          return null;

        return payload;
      },
      metadata_payload() {
        let payload = {};
        if (this.edit_name != this.schedule.name)
          payload.name = this.edit_name;
        if (this.edit_category != this.schedule.category)
          payload.category = this.edit_category;
        if (this.edit_language_code != this.schedule.language.code)
          payload.language = this.languages.filter(function (language) { return language.code == this.edit_language_code }.bind(this))[0];
        if (this.edit_enabled != this.schedule.enabled)
          payload.enabled = this.edit_enabled;
        if (this.edit_warehouse_path != this.schedule.config.warehouse_path)
          payload.warehouse_path = this.edit_warehouse_path;
        if (this.edit_tags != this.schedule.tags)
          payload.tags = this.edit_tags;

        if (Object.keys(payload).length == 0)
          return null;
        return payload;
      },
      offliner_payload() {
        let payload = {};
        if (this.edit_task_name != this.schedule.config.task_name)
          payload.task_name = this.edit_task_name;
        if (this.edit_image_name != this.schedule.config.image.name || this.edit_image_tag != this.schedule.config.image.tag)
          payload.image = {name: this.edit_image_name, tag: this.edit_image_tag};
        if (this.edit_cpu != this.schedule.config.resources.cpu || this.edit_memory != this.schedule.config.resources.memory || this.edit_disk != this.schedule.config.resources.disk)
          payload.resources = {cpu: this.edit_cpu, memory: this.edit_memory, disk: this.edit_disk};
        if (this.flags_payload) {
          payload.flags = this.flags_payload;
        }

        if (Object.keys(payload).length == 0)
          return null;
        return payload;
      },
      payload() {
        let payload = {};
        if (this.metadata_payload)
          Object.assign(payload, this.metadata_payload);
        if (this.offliner_payload)
          Object.assign(payload, this.offliner_payload);
        if (this.flags_payload)
          Object.assign(payload, {"flags": this.flags_payload});

        if (Object.keys(payload).length == 0)
          return null;
        return payload;
      },
      memoryOptions() {
        return Constants.memory_values.map(function (value) { return {text: Constants.filesize(value), value: value}; });
      },
      diskOptions() {
        let values = Constants.disk_values;
        if (values.indexOf(this.edit_disk) == -1)
          values.push(this.edit_disk);
        return values.map(function (value) { return {text: Constants.filesize(value), value: value}; });
      },
      categoriesOptions() {
        return Constants.categories.map(function (category) { return {text: category, value: category}; });
      },
      warehouse_pathsOptions() {
        return Constants.warehouse_paths.map(function (warehouse_path) { return {text: warehouse_path, value: warehouse_path}; });
      },
      offlinersOptions() {
        return Constants.offliners.map(function (offliner) { return {text: offliner, value: offliner}; });
      },
      languagesOptions() {
        return this.languages.map(function (language) { return {text: language.name_en, value: language.code}; });
      },
      tagsOptions() {
        return this.tags.map(function (tag) { return {text: tag, value: tag}; });
      },
      canEditSchedule() { return this.$store.getters.isLoggedIn && this.edit_name !== null; },
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
      commit_form() {
        console.log("COMMIT");

        if (this.payload === null) {
          console.log("nothing to commit");
          return;
        }

        console.log("About to commit", this.payload)

        let parent = this;
        parent.toggleLoader("commiting updates…");
        parent.$root.axios.patch('/schedules/' + this.schedule_name, parent.payload)
        .then(function () {
            let msg = "Recipe updated successfuly.";
            parent.$root.$emit('feedback-message', 'success', "<strong>Updated!</strong><br />" + msg);
            if (parent.payload.name !== undefined) {  // named changed so we need to redirect
              parent.$router.push({name: 'schedule-detail-tab',
                                   params: {schedule_name: parent.payload.name, selectedTab: 'edit'}});
            }
            parent.update_from_metadata(parent.payload);
            parent.update_from_offliner(parent.payload);
        })
        .catch(function (error) {
          if (error.response.status == 400) {
            console.log(error.response.data);
            let msg = "";
            msg += "<br />" + error.response.data.error;
            msg += "<br />" + error.response.data.error_description;
            parent.$root.$emit('feedback-message', 'warning', Constants.standardHTTPError(error.response) + msg);
          } else {
            parent.$root.$emit('feedback-message', 'danger', Constants.standardHTTPError(error.response));
          }
        })
        .then(function () {
            parent.toggleLoader(false);
            parent.scrollToTop();
        });

      },
      reset_form() {
        console.log("RESET");
      },
      filesize(value) { return Constants.filesize(parseInt(value)); },
      reset_metadata() {
          this.edit_name = this.schedule.name;
          this.edit_category = this.schedule.category;
          this.edit_language_code = this.schedule.language.code;
          this.edit_enabled = this.schedule.enabled;
          this.edit_warehouse_path = this.schedule.config.warehouse_path;
          this.edit_tags = this.schedule.tags;
      },
      reset_offliner() {
        this.edit_task_name = this.schedule.config.task_name;
        this.edit_image_name = this.schedule.config.image.name;
        this.edit_image_tag = this.schedule.config.image.tag;
        this.edit_cpu = this.schedule.config.resources.cpu;
        this.edit_memory = this.schedule.config.resources.memory;
        this.edit_disk = this.schedule.config.resources.disk;
        this.edit_flags = Constants.duplicate(this.schedule.config.flags);
      },
      update_from_metadata(payload) {
        if (payload.name !== undefined && payload.name != this.schedule.name)
          this.schedule.name = payload.name;
        if (payload.category !== undefined && payload.category != this.schedule.category)
          this.schedule.category = payload.category;
        if (payload.language !== undefined && payload.language != this.schedule.language.code)
          this.schedule.language = this.languages.filter(function (language) { return language.code == payload.language }.bind(this))[0];
        if (payload.enabled !== undefined && payload.enabled != this.schedule.enabled)
          this.schedule.enabled = payload.enabled;
        if (payload.warehouse_path !== undefined && payload.warehouse_path != this.schedule.config.warehouse_path)
          this.schedule.config.warehouse_path = payload.warehouse_path;
        if (payload.tags !== undefined && payload.tags != this.schedule.tags)
          this.schedule.tags = payload.tags;

        this.reset_metadata();
      },
      update_from_offliner(payload) {
        if (payload.task_name !== undefined && payload.task_name != this.schedule.config.task_name)
          this.schedule.config.task_name = payload.task_name;
        if (payload.image !== undefined && payload.image != this.schedule.config.image)
          this.schedule.config.image = payload.image;
        if (payload.resources !== undefined && payload.resources != this.schedule.config.resources)
          this.schedule.config.resources = payload.resources;

        this.reset_metadata();
      },
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
      loadLanguages() {
        let parent = this;
        parent.$root.axios.get('/languages/', {params: {limit: 200}})
            .then(function (response) {
              for (var i=0; i<response.data.items.length; i++){
                parent.languages.push(response.data.items[i]);
              }
            })
            .catch(function (error) {
              console.error("unable to fetch languages.", error);
              return;
            });
      },
      loadTags() {
        let parent = this;
        parent.$root.axios.get('/tags/', {params: {limit: 200}})
          .then(function (response) {
            for (var i=0; i<response.data.items.length; i++){
              parent.tags.push(response.data.items[i]);
            }
          })
          .catch(function (error) {
            console.error("can't load tags.", error);
            return;
          });
      },
      loadFlagDefnition() {
        let parent = this;
        parent.$root.axios.get('/offliners/' + parent.edit_task_name)
          .then(function (response) {
            parent.flags_definition = response.data;
            parent.reset_offliner();
          })
          .catch(function (error) {
            console.error("can't load flags def.", error);
            return;
          });
      }
    },
    mounted() {
      let parent = this;

      parent.toggleLoader("fetching schedule…");
      parent.$root.axios.get('/schedules/' + this.schedule_name)
        .then(function (response) {
            parent.error = null;

            parent.schedule = response.data;
            parent.reset_metadata();
            parent.reset_offliner();
            if (parent.schedule.most_recent_task) {
              parent.schedule.most_recent_task.on = moment(parent.schedule.most_recent_task.updated_at).fromNow();
            }
        })
        .catch(function (error) {
          parent.error = Constants.standardHTTPError(error.response);
        })
        .then(function () {
            parent.toggleLoader(false);
            parent.loadLanguages();
            parent.loadTags();
            parent.loadFlagDefnition();
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


<style type="text/css" scoped>
  .edit-tab {
    padding: 1rem;
  }

  .form-control, .custom-select {
    color: blue;
  }
</style>
