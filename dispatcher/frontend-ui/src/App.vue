<template>
  <div id="app">
    <NavBar />
    <AlertFeedback />
    <router-view />
  </div>
</template>

<script type="text/javascript">
  import axios from 'axios'

  import Constants from './constants.js'
  import ZimfarmMixins from './components/Mixins.js'
  import NavBar from './components/NavBar.vue'
  import AlertFeedback from './components/AlertFeedback.vue'

  export default {
    name: 'app',
    mixins: [ZimfarmMixins],
    components: {NavBar, AlertFeedback},
    methods: {
      loadLanguages() {
        let parent = this;
        // download languages
        if (!parent.$store.getters.languages.length) {
          this.toggleLoader("fetching languages…");
          parent.queryAPI('get', '/languages/', {params: {limit: 400}})
            .then(function (response) {
              let languages = [];
              for (var i=0; i<response.data.items.length; i++){
                languages.push(response.data.items[i]);
              }
              parent.$store.dispatch('setLanguages', languages);
            })
            .catch(function (error) {
              parent.alertDanger("Unable to fetch languages",  Constants.standardHTTPError(error.response));
              return;
            }).then(function () {
              parent.toggleLoader(false);
            });
        }
      },
      loadTags() {
        let parent = this;
        // download tags
        if (!parent.$store.getters.tags.length) {
          this.toggleLoader("fetching tags…");
          parent.queryAPI('get', '/tags/', {params: {limit: 100}})
            .then(function (response) {
              let tags = [];
              for (var i=0; i<response.data.items.length; i++){
                tags.push(response.data.items[i]);
              }
              parent.$store.dispatch('setTags', tags);
            })
            .catch(function (error) {
              parent.alertDanger("Unable to fetch tags", Constants.standardHTTPError(error.response));
              return;
            }).then(function () {
              parent.toggleLoader(false);
            });
        }
      },
      loadOffliners() {
        let parent = this;
        // download offliners
        if (!parent.$store.getters.offliners.length) {
          this.toggleLoader("fetching offliners…");
          parent.queryAPI('get', '/offliners/', {params: {limit: 100}})
            .then(function (response) {
              let offliners = [];
              for (var i=0; i<response.data.items.length; i++){
                offliners.push(response.data.items[i]);
              }
              parent.$store.dispatch('setOffliners', offliners);
              parent.loadOfflinersDefs();
            })
            .catch(function (error) {
              parent.alertDanger("Unable to fetch offliners", Constants.standardHTTPError(error.response));
              return;
            }).then(function () {
              parent.toggleLoader(false);
            });
        }
      },
      async loadOfflinersDefs() {
        let parent = this;
        // download offliners defs
        if (!parent.$store.getters.offliners_defs.length) {
          this.toggleLoader("fetching offliners defs…");

          let requests = parent.$store.getters.offliners.map(function (offliner) {
            return parent.queryAPI('get', '/offliners/' + offliner);
          });
          let results = await axios.all(requests);
          let definitions = {};
          parent.$store.getters.offliners.forEach(function (offliner, index) {
            definitions[offliner] = results[index].data;
          });
          parent.$store.dispatch('setOfflinersDefs', definitions);
        }
      },
      loadMetaData() {  // load languages and tags metadata from API then launch loadSchedules
        this.loadLanguages();
        this.loadTags();
        this.loadOffliners();
      },
      loadSchedule(schedule_name, force_reload, on_success, on_error) {
        if (!force_reload && this.$store.getters.schedule && this.$store.getters.schedule.name == schedule_name){
          if (on_success) { on_success(); }
          return;
        }

        let parent = this;

        parent.$store.dispatch('clearSchedule');  // reset until we receive the right schedule
        parent.toggleLoader("fetching schedule…");
        parent.queryAPI('get', '/schedules/' + schedule_name)
          .then(function (response) {
              // parent.error = null;
              let schedule = response.data;
              parent.$store.dispatch('setSchedule', schedule);

              if (on_success) { on_success(); }
          })
          .catch(function (error) {
            if (on_error) { on_error(Constants.standardHTTPError(error.response)); }
          })
          .then(function () {
              parent.toggleLoader(false);
          });
      }
    },
    beforeMount() {
      this.loadTokenFromCookie();
      this.$root.$on('load-schedule', this.loadSchedule);
    },
    mounted() {
      this.loadMetaData();
    },
  }
</script>
