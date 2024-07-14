# -*- coding: utf-8 -*-
from obswebsocket import obsws, requests, events, exceptions
from .logger import LoggerConfig

class OBSController():
    def __init__(self,  host:str, port:int, password:str):
        self.ws = obsws(host, port, password)
        self.logger = LoggerConfig.get_logger(self.__class__.__name__)

    # deco
    def connection(func):
        def _wrapper(self, *args, **kwargs):
            try:
                self.ws.connect()
                return func(self, *args, **kwargs)
            except Exception as e:
                print(f"Error: {e}")
                return False
            finally:
                self.ws.disconnect()
        return _wrapper

    @connection
    def start_streaming(self):
        response = self.ws.call(requests.StartStream())
        self.logger.info("Streaming started")
        return response

    @connection
    def stop_streaming(self):
        response = self.ws.call(requests.StopStream())
        self.logger.info("Streaming stopped")
        return response

    @connection
    def set_scene(self, scene_name):
        response = self.ws.call(requests.SetCurrentProgramScene(sceneName=scene_name))
        self.logger.info(f"Scene set to {scene_name}")
        return response

    @connection
    def show_source(self, scene_name, source_name):
        scene_item_id = self.get_scene_item_id(scene_name, source_name)
        if scene_item_id:
            response = self.ws.call(requests.SetSceneItemEnabled(
                sceneName=scene_name,
                sceneItemId=scene_item_id,
                sceneItemEnabled=True ))
            self.logger.info(f"Source {source_name} visible")
            return response
        else:
            self.logger.error("Error specified source name does not exist.")
            return False

    @connection
    def hide_source(self, scene_name, source_name):
        scene_item_id = self.get_scene_item_id(scene_name, source_name)
        if scene_item_id:
            response = self.ws.call(requests.SetSceneItemEnabled(
                sceneName=scene_name,
                sceneItemId=scene_item_id,
                sceneItemEnabled=False ))
            self.logger.info(f"Source {source_name} hidden")
            return response
        else:
            self.logger.error("Error specified source name does not exist.")
            return False

    @connection
    def set_source_in_scene_visibility(self, scene_name, source_name, visibility):
        scene_item_id = self.get_scene_item_id(scene_name, source_name)
        # scene_item_id = self.get_scene_item_id_in_current_scene(source_name)
        print(scene_item_id)
        visibility = True if visibility == 'visible' else False
        if scene_item_id:
            response = self.ws.call(requests.SetSceneItemEnabled(
                sceneName=scene_name,
                sceneItemId=scene_item_id,
                sceneItemEnabled=visibility ))
            state = 'visible' if visibility else 'hidden'
            self.logger.info(f"Source '{source_name}' in scene '{scene_name}' is now {state}")
            return response
        else:
            self.logger.error("Error specified source name does not exist.")
            return False

    @connection
    def set_text_source(self, source_name, new_text):
        response = self.ws.call(requests.GetInputSettings(inputName=source_name))
        settings = response.getInputSettings()
        settings['text'] = new_text
        response = self.ws.call(requests.SetInputSettings(inputName=source_name, inputSettings=settings))
        return response

    @connection
    def get_current_scene_name(self):
        response = self.ws.call(requests.GetCurrentProgramScene())
        return response.getSceneName()

    # 現在のシーン内で、与えられたソース(scene_item)のid(sceneItemnId)を取得する
    @connection
    def get_scene_item_id_in_current_scene(self, source_name):
        response1 = self.ws.call(requests.GetCurrentProgramScene())
        scene_name = response1.getSceneName()
        response2 = self.ws.call(requests.GetSceneItemId(sceneName=scene_name, sourceName=source_name))
        scene_item_id = response2.getSceneItemId()
        return scene_item_id

    @connection
    def get_scene_item_id(self, source_name):
        scene_list = self.ws.call(requests.GetSceneList())
        scenes = scene_list.getScenes()
        for scene in scenes:
            scene_name = scene['sceneName']
            try:
                response = self.ws.call(requests.GetSceneItemId(sceneName=scene_name, sourceName=source_name))
                scene_item_id = response.getSceneItemId()
                return scene_item_id
            except Exception:
                continue
        return False

    @connection
    def get_stream_status(self):
        status = self.ws.call(requests.GetStreamStatus())
        self.is_streaming = status.getStreaming()
        self.logger.info(f"Streaming status: {self.is_streaming}")
