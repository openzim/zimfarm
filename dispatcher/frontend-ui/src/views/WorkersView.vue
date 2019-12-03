<!-- Placeholder view for listing workers and their current statuses: needs API update -->

<template>
  <div class="container">
    <p class="alert alert-info">this information is not up-to-date.</p>
    <table v-if="!error" class="table table-responsive-sm table-striped table-hover">
      <thead class="thead-dark">
        <tr><th>Name</th><th>Status</th></tr>
      </thead>
      <tbody>
        <tr v-for="worker in workers" :key="worker.name">
          <td>{{ worker.hostname }}</td>
          <td>{{ worker.status }}</td>
        </tr>
      </tbody>
    </table>
    <ErrorMessage :message="error" v-else />
  </div>
</template>

<script type="text/javascript">
  import Constants from '../constants.js'
  import ZimfarmMixins from '../components/Mixins.js'
  import ErrorMessage from '../components/ErrorMessage.vue'

  export default {
    name: 'WorkersView',
    mixins: [ZimfarmMixins],
    components: {ErrorMessage},
    data: function () {
      return {
        error: null,  // API generated error
        workers: [],  // list of workers as returned by API
      };
    },
    methods: {
      loadWorkersList: function() {  // load workers list from API
        let parent = this;

        parent.toggleLoader("fetching workers…");
        parent.$root.axios.get('/workers/')
          .then(function (response) {
            parent.error = null;
            parent.workers = [];
            for (var i=0; i<response.data.items.length; i++){
              parent.workers.push(response.data.items[i]);
            }
          })
          .catch(function (error) {
            parent.error = Constants.standardHTTPError(error.response);
          })
          .then(function () {
            parent.toggleLoader(false);
          });
      },
    },
    mounted: function() {
      this.loadWorkersList();
    },
  }
</script>
