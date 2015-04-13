import requests
from copy import copy
import re
import csv
from lxml.html import fromstring

def parse_doc(doc):
    for item in doc.xpath('//tr[td[2][@valign and br]]'):
        nome_cognome,titolo=item.xpath('td[2]/text()')
        nome_cognome=nome_cognome.strip()
        nome=nome_cognome.split(' ')[:-1]
        nome=' '.join(nome)
        cognome=nome_cognome.split(' ')[-1]
        titolo=titolo.strip()[len('Titolo studio: '):]
        telefono=item.xpath('td[4]/text()')[0]
        email=item.xpath('td[5]/a/@href')[0][len('mailto:'):]
        indirizzo=item.xpath('td[3]/text()')[0]
        regexp=r"(?P<indirizzo>.*),\s(?P<cap>[\d\w]{1,})\s(?P<comune>[\w\s'\-`]+)\s\((?P<provincia>[\w\s'\-`]+)\),"
        p=re.compile(regexp)
        m=p.search(indirizzo)
        if not m:
            yield [titolo,nome,cognome,email,telefono,None,None,None,indirizzo]
        indirizzo=m.group('indirizzo')
        cap=m.group('cap')
        comune=m.group('comune')
        provincia=m.group('provincia')
        yield [titolo,nome,cognome,email,telefono,comune,provincia,cap,indirizzo]

BASEURL='http://www.cened.it/mappa_certificatore?p_p_id=EXT_B80_MALO_INSTANCE_FNBN&p_p_lifecycle=0&p_p_state=normal&p_p_mode=view&p_p_col_id=colonna-2&p_p_col_pos=1&p_p_col_count=2&tabs1=Ricerca%20per%20provincia%20e%20comune%20o%20per%20nominativo'
s=requests.Session()
s.headers.update({'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:37.0) Gecko/20100101 Firefox/37.0'})
r=s.get(BASEURL)
cookies=r.cookies
doc=fromstring(r.content)
XPATH='''//form/select/option'''
values=[]
for item in doc.xpath(XPATH):
    if item.text!='...':
        value=item.attrib.get('value') # same as item.text but just to be sure.
        values.append(value)
with open('result.csv','wb') as outfile:
    writer=csv.writer(outfile)
    writer.writerow(['Titolo','Nome','Cognome','Email','Telefono','Comune','Provincia','CAP','Indirizzo'])
    for value in values:
        print "Processing provincia {:30}".format(value),
        headers={'Referer': BASEURL,'Content-Type':'application/x-www-form-urlencoded'}
        data={'malo.cityid':'',
            'malo.cityname':'',
            'malo.districtid':value,
            'malo.districtname':value,
            'malo.extprop1':'null',
            'malo.extprop2':'null',
            'malo.name':'',
            'malo.searchtype':'provinceandcity',
            'tabs1':'Ricerca per provincia e comune o per nominativo'}
        pass
        params={'_EXT_B80_MALO_INSTANCE_FNBN_struts_action':'/malo/view',
            '_EXT_B80_MALO_INSTANCE_FNBN_tabs1':'Ricerca per provincia e comune o per nominativo',
            'p_p_col_count':'2',
            'p_p_col_id':'colonna-2',
            'p_p_col_pos':'1',
            'p_p_id':'EXT_B80_MALO_INSTANCE_FNBN',
            'p_p_lifecycle':'0',
            'p_p_mode':'view',
            'p_p_state':'normal',}
        r=s.post('http://www.cened.it/mappa_certificatore',params=params,data=data,headers=headers,cookies=cookies)
        doc=fromstring(r.content)
        for line in parse_doc(doc):
            writer.writerow(map(lambda x:x.encode('utf-8'),line))
        pagecount=doc.xpath('//div[@class="page-selector"]/text()')[-1]
        pagecount=pagecount.strip().split('di ')[-1]
        pagecount=int(pagecount)
        print "pages:{:3}".format(pagecount),
        for page in xrange(2,pagecount+1):
            data_next=copy(data)
            data_next['malo.actiontype']='PAGINATION'
            data_next['malo.pgnum']=str(page)
            data_next['malo.selpgnum']=str(page)
            r=s.post('http://www.cened.it/mappa_certificatore',params=params,data=data_next,headers=headers,cookies=cookies)
            doc=fromstring(r.content)
            for line in parse_doc(doc):
                writer.writerow(map(lambda x:x.encode('utf-8'),line))
        print "done."
