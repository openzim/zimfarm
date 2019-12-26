<template>
  <div class="container about">
    <h2><img :src="publicPath + 'assets/logo.svg'" /> What's the Zimfarm ?</h2>
    <p><strong>Zimfarm</strong> is <a target="_blank" href="https://kiwix.org">Kiwix</a> and <a target="_blank" href="https://openzim.org">OpenZIM</a>'s platform for automating the creation and re-creation (updates) of <a href="https://wiki.openzim.org/wiki/ZIM_File_Format">ZIM files</a>.</p>
    <p>Our catalog is composed of a thousand <router-link :to="{name: 'schedules-list'}">recipes</router-link> which usually creates several flavoured <a target="_blank" href="http://download.kiwix.org/zim/">ZIM files</a>. ZIM files are built by a selection of <router-link :to="{name: 'workers'}">workers</router-link>.</p>
    <hr />
    <p>Zimfarm is a Python project hosted <a target="_blank" href="https://github.com/openzim/zimfarm">on github</a>. It is built on top of content-specific scrapers like <code>mwoffliner</code>, <code>youtube</code>, <code>sotoki</code>, and others. Check <a target="_blank" href="https://github.com/openzim">OpenZIM's repos</a> for a complete list.</p>
    <p>You can also support this work and speed up the process by providing us a worker.</p>
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
