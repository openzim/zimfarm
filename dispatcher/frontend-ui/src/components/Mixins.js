
// common mixins

export default {
  methods: {
    toggleLoader: function(text) { // shortcut to store's loader status changer
        let payload = text ? {status: true, text: text} : {status: false};
        this.$store.dispatch('setLoading', payload);
      },
    },
}
