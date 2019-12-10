
import Vue from 'vue'
import Vuex from 'vuex'

Vue.use(Vuex);

import moment from 'moment';

const store = new Vuex.Store({
  state: {
    loading: false,
    loading_text: "",
    token: {},
  },
  mutations: {
    setLoading (state, payload) { // toggle GUI loader
      state.loading = payload.status;
      state.loading_text = payload.text ? payload.text : "";
    },
    saveAuthenticationToken(state, payload) { // record full token data
      state.token = payload;
    },
    clearAuthentication(state) { // remove token data completely
      state.token = {};
    }
  },
  actions: {
    setLoading(context, payload) {
      context.commit('setLoading', payload);
    },
    saveAuthenticationToken(context, payload) {
      context.commit('saveAuthenticationToken', payload);
    },
    clearAuthentication(context) {
      context.commit('clearAuthentication');
    }
  },
  getters: {
    loadingStatus(state) { return {should_display: state.loading, text: state.loading_text};},
    username(state) { return state.token.username || null },
    access_token(state) { return state.token.access_token || null },
    token_expiry(state) { return moment(state.token.expires_on) || null },
    token_expired(state) { return moment().isAfter(state.token.expires_on) },
    isLoggedIn(state) {
      // TODO: improv.
      try { return Boolean(state.token.username.length); } catch { return false; }
    },
  }
})

export default store;
