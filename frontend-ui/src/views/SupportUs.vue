<template>
  <div class="container about">
    <h2>Support Zimfarm <img :src="publicPath + 'assets/logo.svg'" /></h2>

    <p>Zimfarm is <a target="_blank" href="https://kiwix.org">Kiwix</a>’ platform for automating the creation and update of <a target="_blank" href="https://wiki.openzim.org/wiki/ZIM_File_Format">ZIM files</a>. Thousands or recipes are run by distributed <router-link :to="{name: 'workers'}">workers</router-link>. All day, every day, so you can enjoy offline content.</p>

    <p>It is <strong>entirely and only supported by donations</strong>. A few dollars may not mean much for you but will certainly help us a lot : if you can, <a target="_blank" href="https://support.kiwix.org/">consider supporting us</a> - even with the price of a cup of coffee (we love coffee and at times need quite a bit of it).</p>

    <p>Another way to help is by <strong>donating a worker</strong> : if you have a GNU/Linux system with at least 4 cores, 2GB of RAM and a fixed public IP, <a target="_blank" href="https://github.com/openzim/zimfarm/blob/master/workers/README.md">follow these instructions</a>. And if you have a headless server you want to give us access to, <a href="mailto:contact+zimfarm@kiwix.org">it's even easier</a>!</p>

    <p>Zimfarm is a Python project hosted <a target="_blank" href="https://github.com/openzim/zimfarm">on Github</a>. It is built on top of content-specific scrapers like <code>mwoffliner</code>, <code>youtube</code>, <code>sotoki</code>, and others. Check out <a target="_blank" href="https://github.com/openzim/zimfarm/blob/master/dispatcher/backend/src/common/schemas/offliners/__init__.py">OpenZIM's repositories</a> for a complete list.</p>
  </div>
</template>

<script type="text/javascript">
  import ZimfarmMixins from '../components/Mixins.js'

  export default {
    name: 'SupportUs',
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
