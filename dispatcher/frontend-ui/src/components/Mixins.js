
import Constants from '../constants.js'

export default {
  data() {
    return {
      selectedLimit: this.getLimitPreference(), // user-defined nb of tasks to retrieve/display
      limits: Constants.LIMIT_CHOICES,
     };
  },
  computed: {
    publicPath() {
      return process.env.BASE_URL;
    },
  },
  methods: {
    scrollToTop() { window.scrollTo(0,0); },
    format_dt(dt) { return Constants.format_dt(dt); },
    toggleLoader(text) { // shortcut to store's loader status changer
      let payload = text ? {status: true, text: text} : {status: false};
      this.$store.dispatch('setLoading', payload);
    },
    getLimitPreference() {
      return this.$cookie.get('pref-limit') || Constants.DEFAULT_LIMIT;
    },
    saveLimitPreference(value) {
      this.$cookie.set('pref-limit', value);
    },
  }
}
