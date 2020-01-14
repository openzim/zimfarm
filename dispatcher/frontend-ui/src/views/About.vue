<template>
  <div class="container about">
    <h2><img :src="publicPath + 'assets/logo.svg'" />About the the Zimfarm</h2>
    <p>The <strong>Zimfarm</strong> is <a target="_blank" href="https://kiwix.org">Kiwix</a> and <a target="_blank" href="https://openzim.org">openZIM</a>'s platform for automating the creation and re-creation (updates) of <a target="_blank" href="https://wiki.openzim.org/wiki/ZIM_File_Format">ZIM files</a>.</p>
    <p>Our catalog is composed of a thousand <router-link :to="{name: 'schedules-list'}">recipes</router-link> which usually creates & publishes several flavoured <a target="_blank" href="https://download.kiwix.org/zim/">ZIM files</a> each. ZIM files are built by a selection of distributed <router-link :to="{name: 'workers'}">workers</router-link>.</p>

    <p>Help us build better ZIM files quicker by providing us a worker. If you have a GNU/Linux system with at least 4 cores and 2GB of RAM, it's easy. You just have to follow <a target="_blank" href="https://github.com/openzim/zimfarm/blob/master/workers/README.md">these instructions</a>. If you have a barbone server you want to give us access to, <a href="mailto:contact+zimfarm@kiwix.org">it's even easier</a>!</p>

    <p>Zimfarm is a Python project hosted <a target="_blank" href="https://github.com/openzim/zimfarm">on Github</a>. It is built on top of content-specific scrapers like <code>mwoffliner</code>, <code>youtube</code>, <code>sotoki</code>, and others. Check <a target="_blank" href="https://github.com/openzim/zimfarm/blob/master/dispatcher/backend/src/common/schemas/offliners/__init__.py">OpenZIM's repos</a> for a complete list.</p>
  </div>
</template>

<script type="text/javascript">
  import ZimfarmMixins from '../components/Mixins.js'

  export default {
    name: 'About',
    mixins: [ZimfarmMixins],
  }
</script>

<style type="text/css">
  .about h2 img {
    width: 2rem;
    height: 2rem;
    margin-bottom: .5rem;
  }
</style>
