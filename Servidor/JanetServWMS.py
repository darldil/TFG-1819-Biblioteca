# -*- coding: utf-8 -*-
"""
Servidor de TFG - Proyecto Janet
Versión 0.1.0

@author: Mauricio Abbati Loureiro - Jose Luis Moreno Varillas
© 2018 Mauricio Abbati Loureiro - Jose Luis Moreno Varillas. All rights reserved.
"""

import urllib
import requests
import json
import lxml.etree as ET
from lxml import html
import io
from authliboclc import wskey

class JanetServWMS():
    
    def buscarLibros(self, datos_consulta):
        
        with open('wskey.conf') as f:
            wskeydata = json.load(f)
            
        URL = "http://www.worldcat.org/webservices/catalog/search/opensearch?"
        
        consulta = {"wskey": wskeydata["key"], "count": 3}
        if 'title' in datos_consulta:
            consulta['q'] = 'srw.ti all "' + datos_consulta['title'] + '"'
        elif 'author' in datos_consulta:
            consulta['q'] = 'srw.au all "' + datos_consulta['author'] + '"'
        else:
            consulta['q'] = 'srw.kw all "' + datos_consulta['generic'] + '"'
        consulta['q'] = consulta['q'] + 'and srw.li all "' + wskeydata["oclc_symbol"]
        consulta['q'] = consulta['q'] + '" and srw.la all "spa"' 
        URL = URL + urllib.parse.urlencode(consulta)
        uh = urllib.request.urlopen(URL)
        content = uh.read()
        
        xmlnamespaces = {'Atom': 'http://www.w3.org/2005/Atom',
                         'oclcterms': 'http://purl.org/oclc/terms/'}
        tree = ET.parse(io.BytesIO(content))
        
        root = tree.getroot()
        
        respuesta = []
        for item in root.findall('Atom:entry', xmlnamespaces):
            temp = {"title": item.find("Atom:title", xmlnamespaces).text, 
                    "author": item.find("Atom:author/Atom:name", xmlnamespaces).text, 
                    "oclc": item.find("oclcterms:recordIdentifier", xmlnamespaces).text}
            temp["cover-art"] = self.buscarCoverArts("https://ucm.on.worldcat.org/oclc/"+ temp["oclc"])
            respuesta.append(temp)
        
        return respuesta
    
    def buscarCoverArts(self, url):
        r = requests.get(url, timeout=5)
        web = html.fromstring(r.content)
        
        return "https:" + web.xpath('//div[@class="coverart"]/img/@ng-src')[0]
        
    def cargarInformacionLibro(self, codigoOCLC):
        
        with open('wskey.conf') as f:
            wskeydata = json.load(f)
            
        URL = "http://www.worldcat.org/webservices/catalog/content/libraries/"
        URL = URL + codigoOCLC + '?'
        
        consulta = {"wskey": wskeydata["key"], "format": "json", 
                    "oclcsymbol": wskeydata["oclc_symbol"], "location": "Spain"}
        URL = URL + urllib.parse.urlencode(consulta)
        
        r = requests.get(url = URL)
        content = r.json()
        
        respuesta = {}
        
        respuesta['response'] = "Aquí tienes el libro que me pediste"
        respuesta['title'] = content['title']
        respuesta['author'] = content['author']
        respuesta['available'] = self.comprobarDisponibilidad(codigoOCLC)
        respuesta['library'] = content['library'][0]['institutionName']
        respuesta['url'] = content['library'][0]['opacUrl']
        respuesta['cover-art'] = self.buscarCoverArts("https://ucm.on.worldcat.org/oclc/" + codigoOCLC)
        
        return respuesta
    
    def comprobarDisponibilidad(self, codigosOCLC):
        with open('wskey.conf') as f:
            wskeydata = json.load(f)
            
        URL = "https://www.worldcat.org/circ/availability/sru/service?"
        URL = URL + "query=no%3Aocm" + codigosOCLC + "&x-registryId=" + wskeydata['registry_id']
        
        APIkey = wskeydata['key']
        secret = wskeydata['secret']
        
        my_wskey = wskey.Wskey(key=APIkey, secret=secret, options=None)
        
        authorization_header = my_wskey.get_hmac_signature(
                method='GET',
                request_url=URL,
                options=None)
        
        r = urllib.request.Request(url = URL, headers={
                'Authorization': authorization_header})
        response = urllib.request.urlopen(r)
        
        content = response.read()
        
        xmlns = {'sRR': 'http://www.loc.gov/zing/srw/'}
        
        tree = ET.parse(io.BytesIO(content))
        
        root = tree.getroot()
        
        for holdings in root.findall('.//sRR:records/sRR:record/sRR:recordData/opacRecord/holdings', xmlns):
            for items in holdings.iterdescendants('holding'):
                for item in items.findall('.//circulation'):
                    if (int(item.find('availableNow').get('value')) > 0): return True
                    
            #codsOCLC.append(item.find("oclcterms:recordIdentifier", xmlnamespaces).text)
        return False