
<template>
    <header>
        <nav class="navbar navbar-expand-md navbar-dark">
            <a class="navbar-brand branding">
                <div class="icon"><img :src="publicPath + 'assets/logo.svg'" />
                <Loading/></div>
                <label>Zimfarm</label>
            </a>

            <b-navbar-toggle target="nav-collapse"></b-navbar-toggle>
             <b-collapse id="nav-collapse" is-nav>
                <ul class="navbar-nav mr-auto text-center mb-md-0 mb-2">
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
                </ul>
                <div class="d-flex align-items-center flex-md-row flex-column">
                    <router-link class="btn btn-light btn-sm mr-md-2 mb-2 mb-md-0" :to="{ name: 'support-us' }">
                        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 16 16" width="16" height="16" style="color: rgb(234, 74, 170) !important; fill: currentColor;"><path fill-rule="evenodd" d="M4.25 2.5c-1.336 0-2.75 1.164-2.75 3 0 2.15 1.58 4.144 3.365 5.682A20.565 20.565 0 008 13.393a20.561 20.561 0 003.135-2.211C12.92 9.644 14.5 7.65 14.5 5.5c0-1.836-1.414-3-2.75-3-1.373 0-2.609.986-3.029 2.456a.75.75 0 01-1.442 0C6.859 3.486 5.623 2.5 4.25 2.5zM8 14.25l-.345.666-.002-.001-.006-.003-.018-.01a7.643 7.643 0 01-.31-.17 22.075 22.075 0 01-3.434-2.414C2.045 10.731 0 8.35 0 5.5 0 2.836 2.086 1 4.25 1 5.797 1 7.153 1.802 8 3.02 8.847 1.802 10.203 1 11.75 1 13.914 1 16 2.836 16 5.5c0 2.85-2.045 5.231-3.885 6.818a22.08 22.08 0 01-3.744 2.584l-.018.01-.006.003h-.002L8 14.25zm0 0l.345.666a.752.752 0 01-.69 0L8 14.25z"></path></svg>
                        <span class="ml-1">Support us</span>
                    </router-link>
                    <UserButton />
                </div>
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