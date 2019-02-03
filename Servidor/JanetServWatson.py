# -*- coding: utf-8 -*-
"""
Servidor de TFG - Proyecto Janet
Versión 0.1.0

@author: Mauricio Abbati Loureiro - Jose Luis Moreno Varillas
© 2018 Mauricio Abbati Loureiro - Jose Luis Moreno Varillas. All rights reserved.
"""
import json
from watson_developer_cloud import AssistantV1

class JanetServWatson():
    
    def consultar(self, client_request):
        respuesta = {}
        with open('credentials.conf') as f:
            data = json.load(f)
        
        service = AssistantV1(
                    version='2018-07-10',
                    ## url is optional, and defaults to the URL below. Use the correct URL for your region.
                    url='https://gateway.watsonplatform.net/assistant/api',
                    username=data["username"],
                    password=data["pass"])
    
        service.set_http_config({'timeout': 100})
        response = service.message(workspace_id=data["workspace_id"], input={'text': client_request["content"]}).get_result()
        
        if not response['entities']:
            respuesta['content-type'] = 'text'
            respuesta['has-extra-data'] = False
        else:
            datosConsulta = self.prepararConsultaWMS(response)
            respuesta['has-extra-data'] = True
            respuesta.setdefault('extra-data', []).append(datosConsulta)
                
        respuesta['response'] = response["output"]["text"][0]
        return respuesta
    
    def prepararConsultaWMS(self, datosWatson):
        datos = {}
        if (datosWatson['intents'][0]['intent'] == 'consulta'):
            if(datosWatson['entities'][0]['entity'] == 'titulo'):
                datos['title'] = datosWatson['context']['resultado']
            elif(datosWatson['entities'][0]['entity'] == 'autores'):
                datos['author'] = datosWatson['context']['resultado']
            else:
                datos['generic'] = datosWatson['context']['resultado']
                
        return datos
            
            
            