<template>
  <div >
    <p>You are about to <strong>create a new recipe</strong> by cloning <code>{{ from }}</code>.</p>
    <p>Enter a (unique) <em>name</em> for this new recipe:</p>
    <b-form inline @submit.prevent="cloneSchedule">
      <b-input class="mt-1 mr-2" autofocus size="sm" v-model="form_name" placeholder="Type new recipe name" />
      <b-button class="mt-1" type="submit" :disabled="!ready" variant="primary" size="sm">create recipe</b-button>
    </b-form>
  </div>
</template>

<script type="text/javascript">
  import Constants from '../constants.js'
  import ZimfarmMixins from '../components/Mixins.js'

  export default {
    name: 'CloneSchedule',
    mixins: [ZimfarmMixins],
    props: {
      from: String
    },
    data() {
      return {
        form_name: "",
      };
    },
    computed: {
      ready() { return this.from && this.form_name && this.from != this.form_name; },
    },
    methods: {
      cloneSchedule() {
        if (!this.ready)
          return;
        let parent = this;
        let payload = {name: this.form_name};
        parent.toggleLoader("Cloning recipe…");
        parent.queryAPI('post', '/schedules/' + parent.from + '/clone', payload)
          .then(function () {
            parent.alertSuccess("Created!", "Recipe <code>"+ payload.name +"</code> has been created off <code>" + parent.from + "</code>.");
            parent.redirectTo('schedule-detail', {schedule_name: payload.name});
          })
          .catch(function (error) {
            parent.alertError(Constants.standardHTTPError(error.response), true);
          })
          .then(function () {
            parent.toggleLoader(false);
          });
      },
    },
  }
</script>
