<!-- Filterable list of schedules with filtered-fire button -->

<template>
  <div class="container">
    <nav class="row">
      <div class="col">
        <input type="text" class="form-control" v-model="selectedName" @change="loadSchedules" placeholder="Name…" />
      </div>
      <div class="col">
        <multiselect v-model="selectedCategoriesOptions"
                     :options="categoriesOptions"
                     :multiple="true"
                     :clear-on-select="true"
                     :preserve-search="true"
                     :searchable="true"
                     :closeOnSelect="true"
                     placeholder="Categories"
                     label="name"
                     track-by="value"
                     @input="loadSchedules">

        </multiselect>
      </div>
      <div class="col">
        <multiselect v-model="selectedLanguagesOptions"
                     :options="languagesOptions"
                     :multiple="true"
                     :clear-on-select="true"
                     :preserve-search="true"
                     :searchable="true"
                     :closeOnSelect="true"
                     placeholder="Languages"
                     label="name"
                     track-by="value"
                     @input="loadSchedules">

        </multiselect>
      </div>
      <div class="col">
        <multiselect v-model="selectedTagsOptions"
                     :options="tagsOptions"
                     :multiple="true"
                     :clear-on-select="true"
                     :preserve-search="true"
                     :searchable="true"
                     :closeOnSelect="true"
                     placeholder="Tags"
                     label="name"
                     track-by="value"
                     @input="loadSchedules">

        </multiselect>
      </div>
    </nav>
    <table v-if="schedules.length" class="table table-responsive-sm table-striped table-hover">
      <caption>Showing max. <select v-model="selectedLimit" @change.prevent="loadSchedules">
          <option v-for="limit in limits" :key="limit" :value="limit">{{ limit }}</option>
        </select> out of <strong>{{ total_results }} results</strong>
      </caption>
      <thead class="thead-dark">
        <tr><th>Name</th><th>Category</th><th>Language</th><th>Offliner</th><th colspan="2">Last Task</th></tr>
      </thead>
      <tbody>
        <tr v-for="schedule in schedules" :key="schedule._id">
          <td>
            <router-link :to="{name: 'schedule-detail', params: {'schedule_name': schedule.name}}">
              {{ schedule.name }}
            </router-link>
          </td>
          <td>{{ schedule.category }}</td>
          <td>{{ schedule.language.name_en }}</td>
          <td>{{ schedule.config.task_name }}</td>
          <td v-if="schedule.most_recent_task">
            <code :class="schedule.class_attr">{{ schedule.most_recent_task.status }}</code>
          </td>
          <td colspan="2" v-else>-</td>
          <td v-if="schedule.most_recent_task" v-tooltip="datetime(schedule.most_recent_task.updated_at)">
            <router-link :to="{name: 'task-detail', params: {_id: schedule.most_recent_task._id}}">
              {{ schedule.most_recent_task.on }}
            </router-link>
          </td>
        </tr>
      </tbody>
    </table>
  </div>
</template>

<script type="text/javascript">
  import moment from 'moment';
  import Multiselect from 'vue-multiselect'

  import Constants from '../constants.js'
  import ZimfarmMixins from '../components/Mixins.js'

  export default {
    name: 'SchedulesList',
    mixins: [ZimfarmMixins],
    components: {Multiselect},
    data: function () {
      return {
        error: null,  // API originated error message
        selectedLimit: 20, // selected number of results to display
        limits: [10, 20, 50, 200],  // hard-coded options for limit
        meta: {}, // API query metadata (count, skip, limit)
        schedules: [],  // list of schedules returned by the API
        categories: ["gutenberg", "other", "phet", "psiram", "stack_exchange",
                     "ted", "vikidia", "wikibooks", "wikinews", "wikipedia",
                     "wikiquote", "wikisource", "wikispecies", "wikiversity",
                     "wikivoyage", "wiktionary"],  // list of categories for fileering
        languages: [],  // list of languages for filtering
        tags: [],  // list of tags for filtering
        selectedName: "",  // entered regexp to match schedule names on
        selectedCategoriesOptions: [],  // multiple-select value for selected languages to filter on (union)
        selectedLanguagesOptions: [],  // multiple-select value for selected languages to filter on (union)
        selectedTagsOptions: [], // multiple-select value for selected tags to filter on (intersection)
      };
    },
    computed: {
      total_results: function() {
        return (this.meta && this.meta.count) ? this.meta.count : 0;
      },
      categoriesOptions: function() {
        let options = [];
        for (var i=0; i<this.categories.length; i++){
          options.push({name: this.categories[i], value: this.categories[i]});
        }
        return options;
      },
      selectedCategories: function() { return this.selectedCategoriesOptions.map((x) => x.value); },
      languagesOptions: function() {
        let options = [];
        for (var i=0; i<this.languages.length; i++){
          options.push({name: this.languages[i].name_en, value: this.languages[i].code});
        }
        return options;
      },
      selectedLanguages: function() { return this.selectedLanguagesOptions.map((x) => x.value); },
      tagsOptions: function() {
        let options = [];
        for (var i=0; i<this.tags.length; i++){
          options.push({name: this.tags[i], value: this.tags[i]});
        }
        return options;
      },
      selectedTags: function() { return this.selectedTagsOptions.map((x) => x.value); },
    },
    methods: {
      datetime: function (date) { // shortcut to datetime formatter
        return Constants.datetime(date);
      },
      loadMetaData: function () {  // load languages and tags metadata from API then launch loadSchedules
        let parent = this;
        parent.error = null;

        // download languages
        this.toggleLoader("fetching languages…");
        parent.$root.axios.get('/languages/', {params: {limit: 1000}})
          .then(function (response) {
            for (var i=0; i<response.data.items.length; i++){
              parent.languages.push(response.data.items[i]);
            }
          })
          .catch(function (error) {
            parent.error = Constants.standardHTTPError(error.response);
            return;
          }).then(function () {
            parent.toggleLoader(false);
          });

        // download tags
        this.toggleLoader("fetching tags…");
        parent.$root.axios.get('/tags/', {params: {limit: 200}})
          .then(function (response) {
            for (var i=0; i<response.data.items.length; i++){
              parent.tags.push(response.data.items[i]);
            }
          })
          .catch(function (error) {
            parent.error = Constants.standardHTTPError(error.response);
            return;
          }).then(function () {
            parent.toggleLoader(false);
          });

          // metadata loaded, load schedules
          this.loadSchedules();
      },
      loadSchedules: function () {  // load filtered schedules from API
        let parent = this;

        this.toggleLoader("fetching schedules…");

        // prepare params for filering
        let params = {limit: parent.selectedLimit};
        if (this.selectedLanguages.filter(item => item.length).length) {
          params.lang = this.selectedLanguages;
        }
        if (this.selectedTags.filter(item => item.length).length) {
          params.tag = this.selectedTags;
        }
        if (this.selectedCategories.filter(item => item.length).length) {
          params.category = this.selectedCategories;
        }
        if (this.selectedName.length) {
          params.name = this.selectedName;
        }

        parent.error = null;
        parent.$root.axios.get('/schedules/', {params: params})
          .then(function (response) {
                parent.schedules = [];
                parent.meta = response.data.meta;

                for (var i=0; i<response.data.items.length; i++){
                  var schedule = response.data.items[i];
                  if (schedule["most_recent_task"]) {

                    schedule["most_recent_task"]["on"] = moment(schedule["most_recent_task"]["updated_at"]).fromNow()
                    if (schedule["most_recent_task"]["status"] == "succeeded") {
                      schedule["class_attr"] = "schedule-suceedeed";
                    } else if (schedule["most_recent_task"]["status"] == "failed") {
                      schedule["class_attr"] = "schedule-failed";
                    }
                  }
                  parent.schedules.push(schedule);
                }
          })
          .catch(function (error) {
            parent.schedules = [];
            parent.error = Constants.standardHTTPError(error.response);
          })
          .then(function () {
            parent.toggleLoader(false);
          });
      },
    },
    beforeMount(){
      this.loadMetaData();
    },
  }
</script>

<style type="text/css" scoped>
  .container table.table {
    margin-top: .5rem;
  }
  .container input[type=text] {
    height: 100%;
  }
</style>

<style src="vue-multiselect/dist/vue-multiselect.min.css"></style>
