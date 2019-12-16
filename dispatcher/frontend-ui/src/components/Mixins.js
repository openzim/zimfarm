
import Constants from '../constants.js'

export default {
  data() {
    return {
      selectedLimit: this.getLimitPreference(), // user-defined nb of tasks to retrieve/display
      limits: Constants.LIMIT_CHOICES,
     };
  },
  computed: {
    publicPath() { return process.env.BASE_URL; },  // for static files linking
    categories() { return Constants.categories; }, // list of categories for filter/edit
    warehouse_paths() { return Constants.warehouse_paths; },  // list of paths for edit
    languages() { return this.$store.getters.languages; },  // list of lang for filter/edit
    tags() { return this.$store.getters.tags; },  // list of tags for filter/edit
    offliners() { return this.$store.getters.offliners; }, // list of offliners for edit
  },
  methods: {
    scrollToTop() { window.scrollTo(0,0); },
    format_dt(dt) { return Constants.format_dt(dt); },
    toggleLoader(text) { // shortcut to store's loader status changer
      let payload = text ? {status: true, text: text} : {status: false};
      this.$store.dispatch('setLoading', payload);
    },
    getLimitPreference() {   // retrieve nb of items to display from cookie
      return this.$cookie.get('pref-limit') || Constants.DEFAULT_LIMIT;
    },
    saveLimitPreference(value) {  // save nb of items to display in a cookie
      this.$cookie.set('pref-limit', value);
    },
  }
}
