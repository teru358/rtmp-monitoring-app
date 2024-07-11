# -*- coding: utf-8 -*-
import asyncio
from obswebsocket import obsws, requests, events, exceptions
from .logger import LoggerConfig

class OBSController():
    def __init__(self,  config_obs):
        self.config_obs = config_obs
        self.host = config_obs['OBS_WS_host']
        self.port = config_obs['OBS_WS_port']
        self.password = config_obs['OBS_WS_Passwd']
        self.scenes_dict = {}  # {scene_name: { source_name: scene_item_id, source_name: scene_item_id, ...}, ...}
        self.logger = LoggerConfig.get_logger(self.__class__.__name__)
        self.monitor = self.OBSMonitor(self.host, self.port, self.password)
        self.ws = None

        # 要 obsの死活確認
        # self._get_scene_item_id_dict()

    def connection(func):
        def wrapper(self, *args, **kwargs):
            try:
                self.connect()
                return func(self, *args, **kwargs)

            except Exception as e:
                print(f"Error: {e}")
                return False

            finally:
                self.disconnect()

        return wrapper


    def connect(self):
        self.ws = obsws(self.host, self.port, self.password)
        self.ws.connect()
        # self.logger.info("Connected to OBS WebSocket")

    def disconnect(self):
        if self.ws:
            self.ws.disconnect()
            self.ws = None
            # self.logger.info("Disconnected from OBS WebSocket")

    @connection
    def start_streaming(self):
        response = lf.ws.call(requests.StartStreaming())
        self.logger.info("Streaming started")
        return response

    @connection
    def stop_streaming(self):
        response = self.ws.call(requests.StopStreaming())
        self.logger.info("Streaming stopped")
        return response

    @connection
    def set_scene(self, scene_name):
        response = self.ws.call(requests.SetCurrentProgramScene(sceneName=scene_name))
        self.logger.info(f"Scene set to {scene_name}")
        return response

    @connection
    def show_source(self, scene_name, source_name):
        scene_item_id = self._get_scene_item_id(scene_name, source_name)
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
        scene_item_id = self._get_scene_item_id(scene_name, source_name)
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
        scene_item_id = self._get_scene_item_id(scene_name, source_name)
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

    def get_streaming_status(self):
        return self.monitor.get_streaming_stat()

    # wrapper from get_streaming_status
    def is_streaming(self):
        return self.monitor.get_streaming_stat()

    # for test
    def is_streaming_true(self):
        return True

    # for test
    def is_streaming_false(self):
        return False

    def start_monitoring(self):
        asyncio.run(self.monitor.connect())

    def stop_monitoring(self):
        asyncio.run(self.monitor.disconnect())

    # RTMP_Low_Bitrate_Source_NameのsceneItemIdを取得しておく
    @connection
    def _get_scene_item_id_dict(self):
        self.connect()
        scenes = self.ws.call(requests.GetSceneList())
        source_name = self.config_obs['RTMP_Low_Bitrate_Source_Name']
        if scenes.status:
            for s in scenes.getScenes():
                sid = self.ws.call(requests.GetSceneItemId(sceneName=s['sceneName'], sourceName=source_name))
                if vars(sid)['status'] :
                    self.scenes_dict[s['sceneName']] = {source_name: sid.datain['sceneItemId']}
        else:
            self.logger.info("Scene ID was missing")
        self.disconnect()

    def _get_scene_item_id(self, scene_name, source_name):
        if scene_name in self.scenes_dict:
            scene_sources = self.scenes_dict[scene_name]
            if source_name in scene_sources:
                return scene_sources[source_name]
        return None

    @connection
    def get_current_scene_name(self):
        response = self.ws.call(requests.GetCurrentProgramScene())
        return response.getSceneName()

    @connection
    def get_scene_item_id_in_current_scene(self, source_name):
        response1 = self.ws.call(requests.GetCurrentProgramScene())
        scene_name = response1.getSceneName()
        response2 = self.ws.call(requests.GetSceneItemId(sceneName=scene_name, sourceName=source_name))
        scene_item_id = response2.getSceneItemId()
        return scene_item_id

    class OBSMonitor:
        def __init__(self, host, port, password):
            self.host = host
            self.port = port
            self.password = password
            self.logger = LoggerConfig.get_logger(self.__class__.__name__)
            self.ws = obsws(self.host, self.port, self.password)
            self.is_streaming = False
            self.loop = asyncio.get_event_loop()

        async def connect(self):
            self.ws.connect()
            self.ws.register(self.on_event)
            self.logger.info("Connected to OBS WebSocket")
            self.loop.create_task(self.monitor_streaming_status())

        async def disconnect(self):
            self.ws.disconnect()
            self.logger.info("Disconnected from OBS WebSocket")

        def on_event(self, event):
            if isinstance(event, events.StreamStarted):
                self.is_streaming = True
                self.logger.info("Stream started")
            elif isinstance(event, events.StreamStopped):
                self.is_streaming = False
                self.logger.info("Stream stopped")

        async def monitor_streaming_status(self):
            while True:
                await asyncio.sleep(1)  # 1秒間隔で監視
                try:
                    status = self.ws.call(requests.GetStreamingStatus())
                    if status.getStreaming() != self.is_streaming:
                        self.is_streaming = status.getStreaming()
                        self.logger.info(f"Streaming status updated: {self.is_streaming}")
                except Exception as e:
                    self.logger.error(f"Error checking streaming status: {e}")

        def get_streaming_stat(self):
            return self.is_streaming
