<template>
  <b-form @submit.prevent="commit_form" @reset.prevent="reset_form" v-if="editorReady">

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
          <b-form-input v-model="edit_schedule.name"
                        id="es_name"
                        type="text"
                        required
                        placeholder="wikipedia_fr_all"
                        size="sm"></b-form-input>
        </b-form-group>
      </b-col>
      <b-col>
        <b-form-group label="Language:" label-for="es_language" description="Use API if wanted language not present.">
          <b-form-select id="es_language"
                         v-model="edit_schedule.language.code"
                         :options="languagesOptions"
                         size="sm"></b-form-select>
        </b-form-group>
      </b-col>
      <b-col>
        <b-form-group label="Tags:" label-for="es_tags" description="Recipe tags, not ZIM tags. Use API to create others.">
          <multiselect v-model="edit_schedule.tags"
                 :options="tags"
                 :multiple="true"
                 :clear-on-select="true"
                 :preserve-search="true"
                 :searchable="true"
                 :closeOnSelect="true"
                 :taggable="true"
                 placeholder="Tags"
                 tag-placeholder="Create as new tag"
                 @tag="addTag"
                 size="sm"></multiselect>
        </b-form-group>
      </b-col>
    </b-row>

    <b-row>
      <b-col>
        <b-form-group label="Category:" label-for="es_category">
          <b-form-select id="es_category"
                         v-model="edit_schedule.category"
                         :options="categoriesOptions"
                         size="sm"></b-form-select>
        </b-form-group>
      </b-col>
      <b-col>
        <b-form-group label="Warehouse Path:" label-for="es_warehouse_path" description="Where to upload files. Usually matches category.">
          <b-form-select id="es_warehouse_path"
                          v-model="edit_schedule.config.warehouse_path"
                          :options="warehouse_pathsOptions"
                          required
                          placeholder="Warehouse Path"
                          size="sm"></b-form-select>
        </b-form-group>
      </b-col>
      <b-col>
        <b-form-group label="Status:" label-for="es_enable" description="Disabled recipe can't be scheduled.">
          <SwitchButton v-model="edit_schedule.enabled">{{ edit_schedule.enabled|yes_no("Enabled", "Disabled") }}</SwitchButton>
        </b-form-group>
      </b-col>
    </b-row>

    <b-row>
      <b-col cols="4">
        <b-form-group label="Periodicity:" label-for="es_periodicity" description="How often to automatically request recipe">
          <b-form-select id="es_periodicity"
                          v-model="edit_schedule.periodicity"
                          :options="periodicityOptions"
                          required
                          placeholder="Periodicity"
                          size="sm"></b-form-select>
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
                         v-model="edit_schedule.config.task_name"
                         :options="offlinersOptions"
                         size="sm"
                         @change="offliner_changed"></b-form-select>
        </b-form-group>
      </b-col>
      <b-col>
        <b-form-group label="Image Name:" label-for="es_image" description="Just the image name (repo/name)">
          <b-form-input v-model="edit_schedule.config.image.name"
                        id="es_image"
                        type="text"
                        required
                        placeholder="openzim/mwoffliner"
                        size="sm"></b-form-input>
        </b-form-group>
      </b-col>
      <b-col>
        <b-form-group label="Image Tag:" label-for="es_imagetag" description="Just the tag name. `latest` usually.">
          <b-form-input v-model="edit_schedule.config.image.tag"
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
          <b-form-input v-model="edit_schedule.config.resources.cpu"
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
                         v-model="edit_schedule.config.resources.memory"
                         :options="memoryOptions"
                         size="sm"></b-form-select>
        </b-form-group>
      </b-col>
      <b-col>
        <b-form-group label="Disk:"
                      label-for="es_disk"
                      description="Required disk space. Use API for custom value.">
          <b-form-select id="es_disk"
                         v-model="edit_schedule.config.resources.disk"
                         :options="diskOptions"
                         size="sm"></b-form-select>
        </b-form-group>
      </b-col>
    </b-row>

    <hr />

    <b-row><b-col><h2><code>{{ edit_task_name}}</code> command flags</h2></b-col></b-row>

    <table class="table table-striped table-hover table-sm table-responsive-md">
      <tbody>
      <tr v-for="field in edit_flags_fields" :key="field.data_key">
        <th>{{ field.label }}<sup v-if="field.required">&nbsp;<font-awesome-icon icon="asterisk" color="red" size="xs" /></sup></th>
        <td>
           <SwitchButton
                v-if="field.component == 'switchbutton'"
                :name="'es_flags_' + field.data_key"
                v-model="edit_flags[field.data_key]">{{ edit_flags[field.data_key]|yes_no("Enabled", "Not set") }}
            </SwitchButton>
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
          <component v-if="field.component != 'multiselect' && field.component != 'switchbutton'"
            :is="field.component"
            :name="'es_flags_' + field.data_key"
            :required="field.required"
            :placeholder="field.placeholder"
            v-model="edit_flags[field.data_key]"
            :style="{backgroundColor: field.bind_color ? edit_flags[field.data_key]: ''}"
            size="sm"
            :step="field.step"
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
          type="submit"
          :disabled="!payload"
          :variant="payload ? 'primary' : 'secondary'">Update Offliner details</b-button>
        <b-button
          type="reset"
          :disabled="!payload"
          :variant="payload ? 'dark' : 'secondary'"
          class="ml-2">Reset</b-button>
      </b-col>
    </b-row>

  </b-form>
  <p v-else>Loading…</p>
</template>

<script type="text/javascript">
  import diff from 'deep-diff';

  import Constants from '../constants.js'
  import ZimfarmMixins from '../components/Mixins.js'
  import SwitchButton from '../components/SwitchButton.vue'

  export default {
    name: 'ScheduleEditor',
    mixins: [ZimfarmMixins],
    components: {SwitchButton},
    props: {
      schedule_name: String,  // the schedule name/ID
    },
    data() {
      return {
        error: null,  // API generated error message
        edit_schedule: null, // data holder for edition
        edit_flags: {}, // flags are handled separately
      };
    },
    computed: {
      schedule() { return this.$store.getters.schedule || null; },
      editorReady() { return this.schedule && this.edit_schedule && this.flags_definition !== null; },
      edit_task_name() { return this.edit_schedule.config.task_name || this.schedule.config.task_name; },
      flags_definition() { return this.$store.getters.offliners_defs[this.edit_task_name] || null },
      edit_flags_fields() {
        let fields = [];
        for (var i=0;i<this.flags_definition.length;i++) {
          let field = this.flags_definition[i];
          let component = "b-form-input";
          let options = null;
          let component_type = null;
          let bind_color = null;
          let step = null;

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
            step = 1;
          }

          if (field.type == "float") {
            component = "b-form-input";
            component_type = "number";
            step = 0.1
          }

          if (field.type == "list-of-string-enum") {
            component = "multiselect";
            options = field.choices;
          }

          if (field.type == "boolean") {
            component = "switchbutton";
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
            step: step,
          });

        }
        return fields;
      },
      flags_payload() {  // payload for edited flags
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
        // strip payload of empty values
        function recursivelyCleanup(obj)
        {
            for (var k in obj)
            {
                if (typeof obj[k] == "object" && obj[k] !== null)
                  recursivelyCleanup(obj[k]);
                else {
                  if (!Object.isArray(obj) && obj[k] == "") {
                    delete obj[k];
                  }
                }
            }
        }
        recursivelyCleanup(payload);
        if (Object.keys(payload).length == 0)
          return null;

        return payload;
      },
      payload() {
        let payload = {};
        let parent = this;

        ["name", "category", "enabled", "periodicity"].forEach(function (key) {
          if (parent.edit_schedule[key] != parent.schedule[key])
            payload[key] = parent.edit_schedule[key];
        });

        // compare tags array
        if (!parent.edit_schedule.tags.isEqual(parent.schedule.tags))
          payload.tags = parent.edit_schedule.tags;

        // language via its code
        if (parent.edit_schedule.language.code != parent.schedule.language.code)
          payload.language = this.languages.filter(function (language) { return language.code == this.edit_schedule.language.code }.bind(this))[0];

        // config properties
        ["warehouse_path", "task_name"].forEach(function (key) {
          if (parent.edit_schedule.config[key] != parent.schedule.config[key])
            payload[key] = parent.edit_schedule.config[key];
        });

        // image is changed alltogether
        if (parent.edit_schedule.config.image.name != parent.schedule.config.image.name ||
              parent.edit_schedule.config.image.tag != parent.schedule.config.image.tag) {
            payload.image = parent.edit_schedule.config.image;
        }

        // resources are changed alltogether
        if (parent.edit_schedule.config.resources.cpu != parent.schedule.config.resources.cpu ||
              parent.edit_schedule.config.resources.memory != parent.schedule.config.resources.memory ||
              parent.edit_schedule.config.resources.disk != parent.schedule.config.resources.disk) {
            payload.resources = parent.edit_schedule.config.resources;
        }

        if (this.flags_payload)
          Object.assign(payload, {"flags": this.flags_payload});

        if (Object.keys(payload).length == 0)
          return null;
        return payload;
      },
      memoryOptions() {
        let values = Constants.memory_values;
        if (values.indexOf(this.edit_schedule.config.resources.memory) == -1)
          values.push(this.edit_schedule.config.resources.memory);
        values.sort(function (a, b) { return a - b;});
        return values.map(function (value) { return {text: Constants.filesize(value), value: value}; });
      },
      diskOptions() {
        let values = Constants.disk_values;
        if (values.indexOf(this.edit_schedule.config.resources.disk) == -1)
          values.push(this.edit_schedule.config.resources.disk);
        values.sort(function (a, b) { return a - b;});
        return values.map(function (value) { return {text: Constants.filesize(value), value: value}; });
      },
      categoriesOptions() {
        return this.categories.map(function (category) { return {text: category, value: category}; });
      },
      warehouse_pathsOptions() {
        return this.warehouse_paths.map(function (warehouse_path) { return {text: warehouse_path, value: warehouse_path}; });
      },
      offlinersOptions() {
        return this.offliners.map(function (offliner) { return {text: offliner, value: offliner}; });
      },
      languagesOptions() {
        return this.languages.map(function (language) { return {text: language.name_en, value: language.code}; });
      },
      tagsOptions() {
        return this.tags.map(function (tag) { return {text: tag, value: tag}; });
      },
      periodicityOptions() {
        return this.periodicities.map(function (periodicity) { return {text: periodicity, value: periodicity}; });
      },
    },
    methods: {
      addTag (new_tag) {
        this.tags.push(new_tag);
        this.edit_schedule.tags.append(new_tag);
      },
      offliner_changed() { // assume flags are different so reset edit schedule
        this.edit_flags = {};
      },
      commit_form() {
        if (this.payload === null) {
          return;
        }

        let parent = this;
        parent.toggleLoader("commiting updates…");
        parent.queryAPI('patch', '/schedules/' + this.schedule_name, parent.payload)
        .then(function () {
            parent.alertSuccess("Updated!", "Recipe updated successfuly.");
            if (parent.payload.name !== undefined) {  // named changed so we need to redirect
              parent.redirectTo('schedule-detail-tab', {schedule_name: parent.payload.name, selectedTab: 'edit'});
              parent.loadSchedule(true, parent.payload.name);
            } else
              parent.loadSchedule(true);
        })
        .catch(function (error) {
          if (error.response.status == 400) {
            parent.alertWarning("Error!", Constants.standardHTTPError(error.response));
          } else {
            parent.alertError(Constants.standardHTTPError(error.response));
          }
        })
        .then(function () {
            parent.toggleLoader(false);
            parent.scrollToTop();
        });

      },
      reset_form() {
        this.edit_schedule = Constants.duplicate(this.schedule);
        this.edit_flags = Constants.duplicate(this.schedule.config.flags);
      },
      loadSchedule(force, schedule_name) {
        let parent = this;
        if (schedule_name === undefined || schedule_name === null)
          schedule_name = parent.schedule_name;

        parent.$root.$emit('load-schedule', schedule_name, force,
            function() { parent.reset_form(); },
            function(error) { console.error(error); parent.alertError(Constants.standardHTTPError(error.response)); });
      },
    },
    mounted() {
      this.loadSchedule(false);
    },
  }
</script>


<style type="text/css" scoped>
  .form-control, .custom-select {
    color: black;
  }
</style>
