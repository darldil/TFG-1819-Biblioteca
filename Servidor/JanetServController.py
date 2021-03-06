# -*- coding: utf-8 -*-
"""
Servidor de TFG - Proyecto Janet
Versión 1.0

@author: Mauricio Abbati Loureiro - Jose Luis Moreno Varillas
© 2018-2019 Mauricio Abbati Loureiro - Jose Luis Moreno Varillas. All rights reserved.
"""
from Actions import ActionConsultaKw, ActionConsultaTitulo, ActionConsultaAutor, ActionConsultaTitAut,\
    ActionConsultaKwAutor, ActionConsultaTel, ActionConsultaLoc, ActionConsultaBuscaMas, ActionConsultaPrimero, \
    ActionConsultaSegundo, ActionConsultaTercero
import JanetServJarvis
import JanetServWMS
import JanetServMongo
import json

class JanetServController:

    def __init__(self, logger):
        self._log = logger
        self._log.info("Iniciando módulo Jarvis")
        self.__pln = JanetServJarvis.JanetServJarvis()
        self._log.info("Jarvis iniciado")
        self._log.info("Iniciando módulo WMS")
        self.__wms = JanetServWMS.JanetServWMS()
        self._log.info("WMS iniciado")
        self._log.info("Iniciando módulo MongoDB")
        self._mongo = JanetServMongo.JanetServMongo()
        self._log.info("MongoDB iniciado")

    def procesarDatos_POST(self, client_request):
        
        respuesta = {}
        asignarID = False

        if 'user_id' not in client_request:
            raise ValueError('No se ha indicado el id del usuario')

        elif client_request["user_id"] == '' or client_request["user_id"] == -1 or client_request["user_id"] == '-1':
            client_request["user_id"] = self._asignarUserId()
            asignarID = True

        if client_request["type"] == "query":
            uid = client_request["user_id"]
            pln = self.__pln.consultar(client_request["content"], uid)

            respuesta = self._tratar_pln(pln['intent'], pln['entities'], pln['message'], uid)
            self._mongo.guardar_timestamp(uid)
            
        elif client_request["type"] == "oclc":
            respuesta.update(self.__wms.cargarInformacionLibro(client_request['content']))
            respuesta['content-type'] = 'single-book'
            self._mongo.guardar_timestamp(client_request["user_id"])

        elif client_request["type"] == "restart":
            uid = client_request["user_id"]
            self._mongo.reiniciar_consulta(uid)
            self.__pln.restart(uid)

        else:
            raise Exception("No se ha especificado un tipo de acción.")

        respuesta["errorno"] = 0
        if asignarID:
            respuesta["user_id"] = client_request["user_id"]

        return json.dumps(respuesta, ensure_ascii=False).encode('utf8')

    def _tratar_pln(self, intent, entities, message, uid):
        respuesta = {}
        respuesta['content-type'] = 'text'
        respuesta['response'] = message
        action = None

        if intent == 'consulta_libros_kw' or intent == 'consulta_libro_kw':
            action = ActionConsultaKw.ActionKw(self._mongo, self.__wms)
        elif intent == 'consulta_libros_titulo' or intent == 'consulta_libro_titulo':
            action = ActionConsultaTitulo.ActionTitle(self._mongo, self.__wms)
        elif intent == 'consulta_libros_autor' or intent == 'consulta_libro_autor':
            action = ActionConsultaAutor.ActionAuthor(self._mongo, self.__wms)
        elif intent == 'consulta_libros_titulo_autor' or intent == 'consulta_libro_titulo_autor':
            action = ActionConsultaTitAut.ActionTitleAuthor(self._mongo, self.__wms)
        elif intent == 'consulta_libros_kw_autor' or intent == 'consulta_libro_kw_autor':
            action = ActionConsultaKwAutor.ActionKwAuthor(self._mongo, self.__wms)
        elif intent == 'consulta_telefono' or intent == 'consulta_telefono_empty':
            action = ActionConsultaTel.ActionPhone(self._mongo, self.__wms)
        elif intent == 'consulta_localizacion' or intent == 'consulta_localizacion_empty':
            action = ActionConsultaLoc.ActionLocation(self._mongo, self.__wms)
        elif intent == 'busca_mas':
            action = ActionConsultaBuscaMas.ActionMoreBooks(self._mongo, self.__wms)
        elif intent == 'mas_info_primero':
            action = ActionConsultaPrimero.ActionFirstBook(self._mongo, self.__wms)
        elif intent == 'mas_info_segundo':
            action = ActionConsultaSegundo.ActionSecondBook(self._mongo, self.__wms)
        elif intent == 'mas_info_tercero':
            action = ActionConsultaTercero.ActionThirdBook(self._mongo, self.__wms)
        else:
            return respuesta

        respuesta = action.accion(intent, entities, respuesta, uid)

        return respuesta

    def _asignarUserId(self):
        ultimoID = self._mongo.obtener_ultimo_id()

        if ultimoID == 0:
            id = 1
            self._mongo.add_usuario(id)
            return id
        else:
            self._mongo.add_usuario(ultimoID + 1)
            return ultimoID + 1
