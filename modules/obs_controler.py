# -*- coding: utf-8 -*-
import asyncio
from obswebsocket import obsws, requests, events
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
        self._get_scene_item_id_dict()

    def connection(func):
        def wrapper():
            self.connect()
            func()
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

    def obs_startup_check(self, timeout=5):
        try:
            self.ws.connect()
            print("Connected to OBS WebSocket.")
            return True
        except obswebsocket.exceptions.ConnectionFailure:
            print("Failed to connect to OBS WebSocket.")
            return False
        except Exception as e:
            print(f"An error occurred: {e}")
            return False

    def start_streaming(self):
        self.connect()
        response = lf.ws.call(requests.StartStreaming())
        self.disconnect()
        self.logger.info("Streaming started")
        return response

    def stop_streaming(self):
        self.connect()
        response = self.ws.call(requests.StopStreaming())
        self.disconnect()
        self.logger.info("Streaming stopped")
        return response

    def set_scene(self, scene_name):
        self.connect()
        response = self.ws.call(requests.SetCurrentProgramScene(sceneName=scene_name))
        self.disconnect()
        self.logger.info(f"Scene set to {scene_name}")
        return response

    def show_source(self, scene_name, source_name):
        scene_item_id = self._get_scene_item_id(scene_name, source_name)
        if scene_item_id:
            self.connect()
            response = self.ws.call(requests.SetSceneItemEnabled(
                sceneName=scene_name,
                sceneItemId=scene_item_id,
                sceneItemEnabled=True ))
            self.disconnect()
            self.logger.info(f"Source {source_name} visible")
            return response
        else:
            self.logger.error("Error specified source name does not exist.")
            return False

    def hide_source(self, scene_name, source_name):
        scene_item_id = self._get_scene_item_id(scene_name, source_name)
        if scene_item_id:
            self.connect()
            response = self.ws.call(requests.SetSceneItemEnabled(
                sceneName=scene_name,
                sceneItemId=scene_item_id,
                sceneItemEnabled=False ))
            self.disconnect()
            self.logger.info(f"Source {source_name} hidden")
            return response
        else:
            self.logger.error("Error specified source name does not exist.")
            return False

    def set_source_in_scene_visibility(self, scene_name, source_name, visibility):
        scene_item_id = self._get_scene_item_id(scene_name, source_name)
        visibility = True if visibility == 'visible' else False
        if scene_item_id:
            self.connect()
            response = self.ws.call(requests.SetSceneItemEnabled(
                sceneName=scene_name,
                sceneItemId=scene_item_id,
                sceneItemEnabled=visibility ))
            self.disconnect()
            state = 'visible' if visibility else 'hidden'
            self.logger.info(f"Source '{source_name}' in scene '{scene_name}' is now {state}")
            return response
        else:
            self.logger.error("Error specified source name does not exist.")
            return False

    def set_text_source(self, source_name, new_text):
        self.connect()
        response = self.ws.call(requests.GetInputSettings(inputName=source_name))
        settings = response.getInputSettings()
        settings['text'] = new_text
        response = self.ws.call(requests.SetInputSettings(inputName=source_name, inputSettings=settings))
        self.disconnect()
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
    def _get_scene_item_id_dict(self):
        self.connect()
        scenes = self.ws.call(requests.GetSceneList())
        source_name = self.config_obs['RTMP_Low_Bitrate_Source_Name']
        if scenes.status:
            for s in scenes.getScenes():
                sid = self.ws.call(requests.GetSceneItemId(
                    sceneName=s['sceneName'],
                    sourceName=source_name ))
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

# クラスの利用例
if __name__ == '__main__':
    obs_controller = OBSController(host='localhost', port=4444, password='your_password')
    obs_controller.start_monitoring()

    # 配信開始
    obs_controller.start_streaming()

    # 5秒待機
    import time
    time.sleep(5)

    # 配信停止
    obs_controller.stop_streaming()

    # 配信状況を確認
    print(f"Streaming status: {obs_controller.get_streaming_status()}")

    # 監視停止
    obs_controller.stop_monitoring()
