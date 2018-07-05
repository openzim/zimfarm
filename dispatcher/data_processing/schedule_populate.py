from html.parser import HTMLParser
from pycountry import languages
import requests


class WikipediaHTMLParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.failed = []

    def handle_starttag(self, tag, attrs):
        if tag == "a":
            attrs = {item[0]: item[1] for item in attrs}
            mw_url = 'https:' + attrs['href']
            try:
                request_json = {
                    "category": "wikipedia",
                    "enabled": True,
                    "language": languages.lookup(attrs['lang']).alpha_3,
                    "name": "wikipedia_{}".format(attrs['lang']),
                    "queue": "tiny",
                    "beat": {
                        "type": "crontab",
                        "config": {
                            "day_of_month": 1,
                            "hour": 7,
                            "minute": 0
                        }
                    },
                    "offliner": {
                        "config": {
                            "adminEmail": "chris@kiwix.org",
                            "mwUrl": mw_url
                        },
                        "name": "mwoffliner"
                    },
                    "task": {
                        "name": "mwoffliner"
                    }
                }
                response = requests.post(
                    url="https://farm.openzim.org/api/schedules/",
                    headers={
                        "token": "",
                        "Content-Type": "application/json; charset=utf-8",
                    },
                    json=request_json
                )
                print(attrs['lang'], response.status_code)

            except LookupError:
                print(attrs['lang'], mw_url)


parser = WikipediaHTMLParser()
parser.feed("""<ul>
<li><a href="//ace.wikipedia.org/" lang="ace">Bahsa Acèh</a></li>
<li><a href="//kbd.wikipedia.org/" lang="kbd" title="Adighabze">Адыгэбзэ</a></li>
<li><a href="//ang.wikipedia.org/" lang="ang">Ænglisc</a></li>
<li><a href="//ab.wikipedia.org/" lang="ab" title="Aṗsua">Аҧсуа</a></li>
<li><a href="//roa-rup.wikipedia.org/" lang="roa-rup">Armãneashce</a></li>
<li><a href="//frp.wikipedia.org/" lang="frp">Arpitan</a></li>
<li><a href="//arc.wikipedia.org/" lang="arc" title="Ātûrāyâ"><bdi dir="rtl">ܐܬܘܪܝܐ</bdi></a></li>
<li><a href="//gn.wikipedia.org/" lang="gn">Avañe’ẽ</a></li>
<li><a href="//av.wikipedia.org/" lang="av" title="Avar">Авар</a></li>
<li><a href="//ay.wikipedia.org/" lang="ay">Aymar</a></li>
<li><a href="//bjn.wikipedia.org/" lang="bjn">Bahasa Banjar</a></li>
<li><a href="//bh.wikipedia.org/" lang="bh" title="Bhōjapurī">भोजपुरी</a></li>
<li><a href="//bcl.wikipedia.org/" lang="bcl">Bikol Central</a></li>
<li><a href="//bi.wikipedia.org/" lang="bi">Bislama</a></li>
<li><a href="//bo.wikipedia.org/" lang="bo" title="Bod Skad">བོད་ཡིག</a></li>
<li><a href="//bxr.wikipedia.org/" lang="bxr" title="Buryad">Буряад</a></li>
<li><a href="//cbk-zam.wikipedia.org/" lang="cbk-x-zam">Chavacano de Zamboanga</a></li>
<li><a href="//co.wikipedia.org/" lang="co">Corsu</a></li>
<li><a href="//za.wikipedia.org/" lang="za">Cuengh</a></li>
<li><a href="//se.wikipedia.org/" lang="se">Davvisámegiella</a></li>
<li><a href="//pdc.wikipedia.org/" lang="pdc">Deitsch</a></li>
<li><a href="//dv.wikipedia.org/" lang="dv" title="Dhivehi"><bdi dir="rtl">ދިވެހިބަސް</bdi></a></li>
<li><a href="//nv.wikipedia.org/" lang="nv">Diné Bizaad</a></li>
<li><a href="//dsb.wikipedia.org/" lang="dsb">Dolnoserbski</a></li>
<li><a href="//myv.wikipedia.org/" lang="myv" title="Erzjanj">Эрзянь</a></li>
<li><a href="//ext.wikipedia.org/" lang="ext">Estremeñu</a></li>
<li><a href="//hif.wikipedia.org/" lang="hif">Fiji Hindi</a></li>
<li><a href="//fur.wikipedia.org/" lang="fur">Furlan</a></li>
<li><a href="//gv.wikipedia.org/" lang="gv">Gaelg</a></li>
<li><a href="//gag.wikipedia.org/" lang="gag">Gagauz</a></li>
<li><a href="//ki.wikipedia.org/" lang="ki">Gĩkũyũ</a></li>
<li><a href="//glk.wikipedia.org/" lang="glk" title="Giləki"><bdi dir="rtl">گیلکی</bdi></a></li>
<li><a href="//gan.wikipedia.org/" lang="gan" title="Gon ua" data-convert-hans="赣语" id="gan_wiki">贛語</a></li>
<li><a href="//hak.wikipedia.org/" lang="hak">Hak-kâ-fa / 客家話</a></li>
<li><a href="//xal.wikipedia.org/" lang="xal" title="Halʹmg">Хальмг</a></li>
<li><a href="//ha.wikipedia.org/" lang="ha"><span lang="ha-Latn">Hausa</span> / <bdi lang="ha-Arab" dir="rtl">هَوُسَا</bdi></a></li>
<li><a href="//haw.wikipedia.org/" lang="haw">ʻŌlelo Hawaiʻi</a></li>
<li><a href="//ig.wikipedia.org/" lang="ig">Igbo</a></li>
<li><a href="//ie.wikipedia.org/" lang="ie">Interlingue</a></li>
<li><a href="//kl.wikipedia.org/" lang="kl">Kalaallisut</a></li>
<li><a href="//pam.wikipedia.org/" lang="pam">Kapampangan</a></li>
<li><a href="//csb.wikipedia.org/" lang="csb">Kaszëbsczi</a></li>
<li><a href="//kw.wikipedia.org/" lang="kw">Kernewek</a></li>
<li><a href="//km.wikipedia.org/" lang="km" title="Phéasa Khmér">ភាសាខ្មែរ</a></li>
<li><a href="//rw.wikipedia.org/" lang="rw">Kinyarwanda</a></li>
<li><a href="//kv.wikipedia.org/" lang="kv" title="Komi">Коми</a></li>
<li><a href="//kg.wikipedia.org/" lang="kg">Kongo</a></li>
<li><a href="//gom.wikipedia.org/" lang="gom">कोंकणी / Konknni</a></li>
<li><a href="//lo.wikipedia.org/" lang="lo" title="Phaasaa Laao">ພາສາລາວ</a></li>
<li><a href="//lad.wikipedia.org/" lang="lad" title="Ladino"><span lang="lad-Latn">Dzhudezmo</span> / <bdi lang="lad-Hebr" dir="rtl">לאדינו</bdi></a></li>
<li><a href="//lbe.wikipedia.org/" lang="lbe" title="Lakːu">Лакку</a></li>
<li><a href="//lez.wikipedia.org/" lang="lez" title="Lezgi">Лезги</a></li>
<li><a href="//lij.wikipedia.org/" lang="lij">Lìgure</a></li>
<li><a href="//ln.wikipedia.org/" lang="ln">Lingála</a></li>
<li><a href="//jbo.wikipedia.org/" lang="jbo">lojban</a></li>
<li><a href="//lrc.wikipedia.org/" lang="lrc" title="Löriyé-Šomālī"><bdi dir="rtl">لۊری شومالی</bdi></a></li>
<li><a href="//lg.wikipedia.org/" lang="lg">Luganda</a></li>
<li><a href="//mt.wikipedia.org/" lang="mt">Malti</a></li>
<li><a href="//zh-classical.wikipedia.org/" lang="lzh" title="Man4jin4 / Wényán">文言</a></li>
<li><a href="//ty.wikipedia.org/" lang="ty">Reo Mā’ohi</a></li>
<li><a href="//mi.wikipedia.org/" lang="mi">Māori</a></li>
<li><a href="//mwl.wikipedia.org/" lang="mwl">Mirandés</a></li>
<li><a href="//mdf.wikipedia.org/" lang="mdf" title="Mokšenj">Мокшень</a></li>
<li><a href="//nah.wikipedia.org/" lang="nah">Nāhuatlahtōlli</a></li>
<li><a href="//na.wikipedia.org/" lang="na">Dorerin Naoero</a></li>
<li><a href="//nds-nl.wikipedia.org/" lang="nds-nl">Nedersaksisch</a></li>
<li><a href="//frr.wikipedia.org/" lang="frr">Nordfriisk</a></li>
<li><a href="//nrm.wikipedia.org/" lang="roa-x-nrm">Nouormand / Normaund</a></li>
<li><a href="//nov.wikipedia.org/" lang="nov">Novial</a></li>
<li><a href="//as.wikipedia.org/" lang="as" title="Ôxômiya">অসমীযা়</a></li>
<li><a href="//pi.wikipedia.org/" lang="pi" title="Pāḷi">पाऴि</a></li>
<li><a href="//pag.wikipedia.org/" lang="pag">Pangasinán</a></li>
<li><a href="//pap.wikipedia.org/" lang="pap">Papiamentu</a></li>
<li><a href="//ps.wikipedia.org/" lang="ps" title="Paʂto"><bdi dir="rtl">پښتو</bdi></a></li>
<li><a href="//koi.wikipedia.org/" lang="koi" title="Perem Komi">Перем Коми</a></li>
<li><a href="//pfl.wikipedia.org/" lang="pfl">Pfälzisch</a></li>
<li><a href="//pcd.wikipedia.org/" lang="pcd">Picard</a></li>
<li><a href="//krc.wikipedia.org/" lang="krc" title="Qaraçay–Malqar">Къарачай–Малкъар</a></li>
<li><a href="//kaa.wikipedia.org/" lang="kaa">Qaraqalpaqsha</a></li>
<li><a href="//crh.wikipedia.org/" lang="crh">Qırımtatarca</a></li>
<li><a href="//ksh.wikipedia.org/" lang="ksh">Ripoarisch</a></li>
<li><a href="//rm.wikipedia.org/" lang="rm">Rumantsch</a></li>
<li><a href="//rue.wikipedia.org/" lang="rue" title="Rusin’skyj Yazyk">Русиньскый Язык</a></li>
<li><a href="//sc.wikipedia.org/" lang="sc">Sardu</a></li>
<li><a href="//stq.wikipedia.org/" lang="stq">Seeltersk</a></li>
<li><a href="//nso.wikipedia.org/" lang="nso">Sesotho sa Leboa</a></li>
<li><a href="//sn.wikipedia.org/" lang="sn">ChiShona</a></li>
<li><a href="//szl.wikipedia.org/" lang="szl">Ślůnski</a></li>
<li><a href="//so.wikipedia.org/" lang="so">Soomaaliga</a></li>
<li><a href="//srn.wikipedia.org/" lang="srn">Sranantongo</a></li>
<li><a href="//kab.wikipedia.org/" lang="kab">Taqbaylit</a></li>
<li><a href="//roa-tara.wikipedia.org/" lang="roa">Tarandíne</a></li>
<li><a href="//tet.wikipedia.org/" lang="tet">Tetun</a></li>
<li><a href="//tpi.wikipedia.org/" lang="tpi">Tok Pisin</a></li>
<li><a href="//to.wikipedia.org/" lang="to">faka Tonga</a></li>
<li><a href="//tk.wikipedia.org/" lang="tk">Türkmençe</a></li>
<li><a href="//tyv.wikipedia.org/" lang="tyv" title="Tyva dyl">Тыва дыл</a></li>
<li><a href="//udm.wikipedia.org/" lang="udm" title="Udmurt">Удмурт</a></li>
<li><a href="//ug.wikipedia.org/" lang="ug"><bdi dir="rtl">ئۇيغۇرچه</bdi></a></li>
<li><a href="//vep.wikipedia.org/" lang="vep">Vepsän</a></li>
<li><a href="//fiu-vro.wikipedia.org/" lang="fiu-vro">Võro</a></li>
<li><a href="//vls.wikipedia.org/" lang="vls">West-Vlams</a></li>
<li><a href="//wo.wikipedia.org/" lang="wo">Wolof</a></li>
<li><a href="//diq.wikipedia.org/" lang="diq">Zazaki</a></li>
<li><a href="//zea.wikipedia.org/" lang="zea">Zeêuws</a></li>
</ul>""")