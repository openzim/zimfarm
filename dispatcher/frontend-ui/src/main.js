import Vue from 'vue'
Vue.config.productionTip = false;

// main dependencies
import VueRouter from 'vue-router'
import VueClipboard from 'vue-clipboard2'
import VueCookie from 'vue-cookie'
import axios from 'axios';

Vue.use(VueRouter);
Vue.use(VueClipboard);
Vue.use(VueCookie);

// Bootstrap
import BootstrapVue from 'bootstrap-vue'
import 'bootstrap/dist/css/bootstrap.css'
import 'bootstrap-vue/dist/bootstrap-vue.css'
Vue.use(BootstrapVue)

import '../public/assets/styles.css'

// Font Awesome
import { library } from '@fortawesome/fontawesome-svg-core'
import { faSpinner, faUser, faUserCircle, faKey, faTimes, faTimesCircle,
         faWrench, faSignInAlt, faSignOutAlt, faArrowCircleLeft,
         faCarrot, faHdd, faMicrochip, faMemory, faCopy, faFire,
         faCalendarAlt, faStopCircle, faTrashAlt, faPlug,
         faSkullCrossbones, faAsterisk, faCheck, faPlusCircle,
         faExclamationTriangle, faServer, faSortAmountUp,
         faExternalLinkAlt } from '@fortawesome/free-solid-svg-icons'
import { FontAwesomeIcon } from '@fortawesome/vue-fontawesome'
library.add(faKey);
library.add(faHdd);
library.add(faUser);
library.add(faPlug);
library.add(faFire);
library.add(faCopy);
library.add(faCheck);
library.add(faServer);
library.add(faTimes);
library.add(faCarrot);
library.add(faMemory);
library.add(faWrench);
library.add(faSpinner);
library.add(faAsterisk);
library.add(faTrashAlt);
library.add(faMicrochip);
library.add(faSignInAlt);
library.add(faSortAmountUp);
library.add(faStopCircle);
library.add(faSignOutAlt);
library.add(faUserCircle);
library.add(faPlusCircle);
library.add(faTimesCircle);
library.add(faCalendarAlt);
library.add(faExternalLinkAlt);
library.add(faArrowCircleLeft);
library.add(faSkullCrossbones);
library.add(faExclamationTriangle);
Vue.component('font-awesome-icon', FontAwesomeIcon);

// Multiselect for schedules filter
import Multiselect from 'vue-multiselect'
Vue.component('multiselect', Multiselect)

// tooltip for hover on loader table heads and durations
import Tooltip from 'vue-directive-tooltip';
import 'vue-directive-tooltip/dist/vueDirectiveTooltip.css';
Vue.use(Tooltip);

// Sugar extensions
import Sugar from 'sugar'
Sugar.extend({namespaces: [Array, Object]});

// Own modules
import App from './App.vue'
import Constants from './constants.js'
import routes from './routes'
import store from './store'  // Vuex store

// Own filters
Vue.filter('filesize', Constants.filesize);
Vue.filter('format_dt', Constants.format_dt);
Vue.filter('from_now', Constants.from_now);
Vue.filter('duration', Constants.format_duration);
Vue.filter('yes_no', Constants.yes_no);
Vue.filter('short_id', Constants.short_id);

// router
const router = new VueRouter({
  mode: 'history',
  base: process.env.BASE_URL,
  linkActiveClass: "active",
  linkExactActiveClass: "exact-active",
  routes:routes,
})

// matomo (stats.kiwix.org)
import VueMatomo from 'vue-matomo'
Vue.use(VueMatomo, {
  host: 'https://stats.kiwix.org',
  siteId: 8,
  trackerFileName: 'matomo',
  router: router,
});

new Vue({
  store: store,
  router: router,
  computed: {
    axios() { // prefixed axios object with API url and token from store
      return axios.create({
          baseURL: Constants.zimfarm_webapi,
          headers: {'Authorization': "Token " + store.getters.access_token},
          paramsSerializer: Constants.params_serializer,
        });
    },
  },
  methods: {
    has_perm(namespace, perm_name) {
      try { return Boolean(this.$store.getters.permissions[namespace][perm_name]); } catch { return false; }
    },
  },
  render: h => h(App),
}).$mount('#app')
