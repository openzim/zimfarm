
<template>
    <header>
        <nav class="navbar navbar-expand-md navbar-dark ">
            <a class="navbar-brand branding">
                <div class="icon"><img :src="publicPath + 'assets/logo.svg'" />
                <Loading/></div>
                <label>Zimfarm</label>
            </a>

            <button class="navbar-toggler" type="button"
                    data-toggle="collapse"
                    data-target="#navbarSupportedContent"
                    aria-controls="navbarSupportedContent"
                    aria-expanded="false"
                    aria-label="Toggle menu">
            <span class="navbar-toggler-icon"></span>
            </button>

            <div class="collapse navbar-collapse" id="navbarSupportedContent">
                <ul class="navbar-nav mr-auto">
                    <li class="nav-item">
                        <router-link class="nav-link" :to="{ name: 'pipeline' }">Pipeline</router-link>
                    </li>
                    <li class="nav-item">
                        <router-link class="nav-link" :to="{ name: 'schedules-list' }">Recipes</router-link>
                    </li>
                    <li class="nav-item disabled">
                        <router-link class="nav-link" :to="{ name: 'workers' }">Workers</router-link>
                    </li>
                    <li class="nav-item" v-show="$store.getters.isLoggedIn">
                        <router-link class="nav-link" :to="{ name: 'users-list' }">Users</router-link>
                    </li>
                    <li class="nav-item disabled">
                        <span class="nav-link" href="/stats">Stats</span>
                    </li>
                </ul>

                <UserButton />
            </div>
        </nav>
    </header>
</template>

<script>
  import Loading from './Loading.vue'
  import UserButton from './UserButton.vue'
  import ZimfarmMixins from './Mixins.js'

  export default {
    name: 'NavBar',
    mixins: [ZimfarmMixins],
    components: {Loading, UserButton},
  }
</script>
