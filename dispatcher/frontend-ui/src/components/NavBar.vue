
<template>
    <header>
        <nav class="navbar navbar-expand-md navbar-dark ">
            <a class="navbar-brand branding">
                <div class="icon"><img :src="publicPath + 'assets/logo.svg'" />
                <Loading/></div>
                <label>Zimfarm</label>
            </a>

            <b-navbar-toggle target="nav-collapse"></b-navbar-toggle>
             <b-collapse id="nav-collapse" is-nav>
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
                    <li class="nav-item" v-show="canReadUsers">
                        <router-link class="nav-link" :to="{ name: 'users-list' }">Users</router-link>
                    </li>
                    <li class="nav-item disabled">
                        <span class="nav-link" href="/stats">Stats</span>
                    </li>
                    <li class="nav-item">
                        <router-link class="nav-link" :to="{ name: 'about' }">About</router-link>
                    </li>
                </ul>
                <UserButton />
            </b-collapse>
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
