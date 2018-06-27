import json
from html.parser import HTMLParser
import requests


class WikipediaListParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.data = []

    def handle_starttag(self, tag, attrs):
        if tag == 'a':
            attrs = {attr[0]: attr[1] for attr in attrs}
            self.data.append(attrs)


class Schedules:
    token = "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJpc3MiOiJkaXNwYXRjaGVyIiwiZXhwIjoxNTI5NDI2MjU1LCJpYXQiOjE1Mjk0MjI2NTUsImp0aSI6ImUyMGVmZDdmLTBlZTQtNGJhMS1iM2VlLTcyZGVkNzRjNjhjYiIsInVzZXIiOnsiX2lkIjoiNWFjMjgxZjQ2ODA5NWEwMDBlNDk0ZWMwIiwidXNlcm5hbWUiOiJhZG1pbiIsInNjb3BlIjp7InVzZXJfbWFuYWdlbWVudCI6eyJjaGFuZ2VfdXNlcm5hbWUiOnRydWUsImNoYW5nZV9lbWFpbCI6dHJ1ZSwiY2hhbmdlX3Bhc3N3b3JkIjp0cnVlfSwidGFzayI6eyJjcmVhdGUiOnRydWUsImRlbGV0ZSI6dHJ1ZX0sInNjaGVkdWxlIjp7ImNyZWF0ZSI6dHJ1ZSwiZGVsZXRlIjp0cnVlLCJ1cGRhdGVfdGFza19jb25maWciOnRydWV9fX19.J_o_O1SOYwfz3RdG3N5XFt14hGwhUdueUf1kbpQKhR8"
    
    def send_request(self, language_code, mw_url, admin_email):
        try:
            response = requests.post(
                url="https://farm.openzim.org/api/schedules/",
                headers={
                    "token": self.token,
                    "Content-Type": "application/json; charset=utf-8",
                },
                data=json.dumps({
                    "language": language_code,
                    "task": {
                        "name": "mwoffliner",
                        "config": {
                            "mwUrl": mw_url,
                            "adminEmail": admin_email
                        }
                    },
                    "offliner": "mwoffliner",
                    "category": "wikipedia",
                    "schedule": {
                        "type": "crontab",
                        "config": {
                            "day_of_month": 1,
                            "minute": 30,
                            "hour": 7
                        }
                    }
                })
            )
            print('Response HTTP Status Code: {status_code}'.format(
                status_code=response.status_code))
            print('Response HTTP Response Body: {content}'.format(
                content=response.content))
        except requests.exceptions.RequestException:
            print('HTTP Request failed')


class WikipediaSchedules(Schedules):
    def __init__(self):
        pass

    def process_100(self):
        html = """
        <ul>
        <li><a href="//ak.wikipedia.org/" lang="ak">Akan</a></li>
        <li><a href="//bm.wikipedia.org/" lang="bm">Bamanankan</a></li>
        <li><a href="//ch.wikipedia.org/" lang="ch">Chamoru</a></li>
        <li><a href="//ny.wikipedia.org/" lang="ny">Chichewa</a></li>
        <li><a href="//ee.wikipedia.org/" lang="ee">Eʋegbe</a></li>
        <li><a href="//ff.wikipedia.org/" lang="ff">Fulfulde</a></li>
        <li><a href="//got.wikipedia.org/" lang="got" title="Gutisk">𐌲𐌿𐍄𐌹𐍃𐌺</a></li>
        <li><a href="//iu.wikipedia.org/" lang="iu">ᐃᓄᒃᑎᑐᑦ / Inuktitut</a></li>
        <li><a href="//ik.wikipedia.org/" lang="ik">Iñupiak</a></li>
        <li><a href="//ks.wikipedia.org/" lang="ks" title="Kashmiri"><bdi dir="rtl">كشميري</bdi></a></li>
        <li><a href="//ltg.wikipedia.org/" lang="ltg">Latgaļu</a></li>
        <li><a href="//fj.wikipedia.org/" lang="fj">Na Vosa Vaka-Viti</a></li>
        <li><a href="//cr.wikipedia.org/" lang="cr">Nēhiyawēwin / ᓀᐦᐃᔭᐍᐏᐣ</a></li>
        <li><a href="//pih.wikipedia.org/" lang="pih">Norfuk / Pitkern</a></li>
        <li><a href="//om.wikipedia.org/" lang="om">Afaan Oromoo</a></li>
        <li><a href="//pnt.wikipedia.org/" lang="pnt" title="Pontiaká">Ποντιακά</a></li>
        <li><a href="//dz.wikipedia.org/" lang="dz" title="Rdzong-Kha">རྫོང་ཁ</a></li>
        <li><a href="//rmy.wikipedia.org/" lang="rmy">Romani</a></li>
        <li><a href="//rn.wikipedia.org/" lang="rn">Kirundi</a></li>
        <li><a href="//sm.wikipedia.org/" lang="sm">Gagana Sāmoa</a></li>
        <li><a href="//sg.wikipedia.org/" lang="sg">Sängö</a></li>
        <li><a href="//st.wikipedia.org/" lang="st">Sesotho</a></li>
        <li><a href="//tn.wikipedia.org/" lang="tn">Setswana</a></li>
        <li><a href="//cu.wikipedia.org/" lang="cu" title="Slověnĭskŭ">Словѣ́ньскъ / ⰔⰎⰑⰂⰡⰐⰠⰔⰍⰟ</a></li>
        <li><a href="//ss.wikipedia.org/" lang="ss">SiSwati</a></li>
        <li><a href="//ti.wikipedia.org/" lang="ti" title="Tigriññā">ትግርኛ</a></li>
        <li><a href="//chr.wikipedia.org/" lang="chr" title="Tsalagi">ᏣᎳᎩ</a></li>
        <li><a href="//chy.wikipedia.org/" lang="chy">Tsėhesenėstsestotse</a></li>
        <li><a href="//ve.wikipedia.org/" lang="ve">Tshivenḓa</a></li>
        <li><a href="//ts.wikipedia.org/" lang="ts">Xitsonga</a></li>
        <li><a href="//tum.wikipedia.org/" lang="tum">chiTumbuka</a></li>
        <li><a href="//tw.wikipedia.org/" lang="tw">Twi</a></li>
        <li><a href="//xh.wikipedia.org/" lang="xh">isiXhosa</a></li>
        <li><a href="//zu.wikipedia.org/" lang="zu">isiZulu</a></li>
        </ul>
        """

        parser = WikipediaListParser()
        parser.feed(html)
        for item in parser.data:
            mw_url = 'https://' + item['href'][2:]
            language_code = item['lang']
            admin_email = 'chris@kiwix.org'

            self.send_request(language_code, mw_url, admin_email)

s = WikipediaSchedules()
s.process_100()
