<!-- Full-featured button to request a selection

  - request a selection
  - disabled if not allowed
  - displays a spinner on click
  - calls the API in the background
  - displays result as an AlertFeedback -->

<template>
  <b-button v-if="!working"
            v-show="canRequestTasks"
            :disabled="disabled"
            class="selection-button"
            size="sm" variant="primary"
            @click.prevent="request_tasks"
            >Request those <strong>{{ nb_schedules}} recipes</strong>
  </b-button>
  <b-button v-else
            class="selection-button"
            size="sm" variant="secondary"
            :disabled="working">
      <font-awesome-icon icon="spinner" size="sm" spin /> {{ working_text}}
    </b-button>
</template>

<script type="text/javascript">
  import Constants from '../constants.js'
  import ZimfarmMixins from '../components/Mixins.js'

  export default {
    name: 'RequestSelectionButton',
    mixins: [ZimfarmMixins],
    props: {
      for_name: String,
      for_categories: Array,
      for_languages: Array,
      for_tags: Array,
      count: Number,
    },
    data() {
      return {
        working_text: null,  // describing text of working action (or null)
        schedules_names: [],
      }
    },
    computed: {
      nb_schedules() { return this.count; },
      disabled() { return (this.nb_schedules < 1 || this.nb_schedules > Constants.MAX_SCHEDULES_IN_SELECTION_REQUEST)},
      working() { return Boolean(this.working_text); },
      should_display_loader() { return this.working; },
    },
    methods: {
      request_tasks() {
        let parent = this;
        parent.working_text = "Requesting tasks…";

        // prepare params for filering
        let params = {limit: Constants.MAX_SCHEDULES_IN_SELECTION_REQUEST};
        if (this.for_name.length) {
          params.name = this.for_name;
        }
        if (this.for_categories.length) {
          params.category = this.for_categories;
        }
        if (this.for_languages.length) {
          params.lang = this.for_languages;
        }
        if (this.for_tags.length) {
          params.tag = this.for_tags;
        }

        parent.queryAPI('get', '/schedules/', {params: params})
          .then(function (response) {
            parent.schedules_names = response.data.items.map(function(item) { return item["name"]});
            parent.do_request_tasks();
          })
          .catch(function (error) {
            parent.alertWarning("Not Requested!",
                                "Unable to fetch recipes names…<br />" + Constants.standardHTTPError(error.response));
            parent.working_text = null;
          })
      },
      do_request_tasks() {
        let parent = this;
        let params = {schedule_names: parent.schedules_names};
        parent.queryAPI('post', '/requested-tasks/', params)
          .then(function (response) {
            let nb_requested = response.data.requested.length;
            let msg = "Exactly <code>" + nb_requested + "</code> recipe(s) matching your selection have been requested.";
            parent.alertSuccess("Requested!", msg, 10);
          })
          .catch(function (error) {
            parent.alertError(Constants.standardHTTPError(error.response));
          })
          .then(function () {
            parent.working_text = null;
          });
      },
    },
  }
</script>

<style type="text/css" scoped>
  .selection-button { float: right; }
</style>
