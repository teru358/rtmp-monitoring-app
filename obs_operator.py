# -*- coding: utf-8 -*-
from modules.obs_controler import OBSController
from modules.obs_monitor import OBSMonitor

class OBSOperator(OBSController):

    def __init__(self, config):
        self.scene_dict = {
            'intro': config['obs']['Scene_Intro'],
            'live':  config['obs']['Scene_Live'],
            'fail':  config['obs']['Scene_Fail'],
            'pause': config['obs']['Scene_Pause']
        }
        self.fail_bw = int(config['obs']['RTMP_Fail_Bitrate'])
        self.stream_previous_scene = None

        connection_settings = {
            'host': config['obs']['OBS_WS_host'],
            'port': int(config['obs']['OBS_WS_port']),
            'password': config['obs']['OBS_WS_Passwd']
        }
        
        super().__init__(**connection_settings)
        self.obs_monitor = OBSMonitor(**connection_settings)
        self.obs_monitor.run()

    # deco
    def obs_is_running(func):
        def _wrapper(self, *args, **kwargs):
            if self.obs_monitor.is_obs_running:
                return func(self, *args, **kwargs)
            else:
                return False
        return _wrapper

    # deco
    def obs_is_streaming(func):
        def _wrapper(self, *args, **kwargs):
            if self.obs_monitor.is_obs_streaming:
                return func(self, *args, **kwargs)
            else:
                return False
        return _wrapper

    # 配信開始
    @obs_is_running
    def stream_start(self):
        response = False
        if self.stream_initialize():
            if not self.obs_monitor.is_obs_streaming:
                response = self.start_streaming()
        return response

    # 配信終了
    @obs_is_running
    def stream_stop(self):
        response = False
        if  self.obs_monitor.is_obs_streaming:
            response = self.stop_streaming()
        return response

    # 初期化
    @obs_is_running
    def stream_initialize(self):
        response = False

        response = self.set_scene(self.scene_dict['intro'])
        if response is not False:
            self.stream_previous_scene = None
        return response

    # intro -> live
    @obs_is_running
    @obs_is_streaming
    def stream_to_live(self):
        response = False
        scene = self._get_scene_id(self.obs_monitor.scene_name)
        response = self.set_scene(self.scene_dict['live'])
        if response is not False:
            self.stream_previous_scene = scene
        return response

    # -> intro
    @obs_is_running
    @obs_is_streaming
    def scene_set_intro(self):
        response = False
        scene = self._get_scene_id(self.obs_monitor.scene_name)
        response = self.set_scene(self.scene_dict['intro'])
        if response is not False:
            self.stream_previous_scene = scene
        return response

    # -> live
    @obs_is_running
    @obs_is_streaming
    def scene_set_live(self):
        response = False
        scene = self._get_scene_id(self.obs_monitor.scene_name)
        response = self.set_scene(self.scene_dict['live'])
        if response is not False:
            self.stream_previous_scene = scene
        return response

    # -> fail
    @obs_is_running
    @obs_is_streaming
    def scene_set_fail(self):
        response = False
        scene = self._get_scene_id(self.obs_monitor.scene_name)
        response = self.set_scene(self.scene_dict['fail'])
        if response is not False:
            self.stream_previous_scene = scene
        return response

    # <-> pause
    @obs_is_running
    @obs_is_streaming
    def scene_switch_pause(self):
        response = False
        scene = self._get_scene_id(self.obs_monitor.scene_name)
        if not scene in ['intro']:
            if scene in ['pause']:
                response = self.set_scene(self.scene_dict[self.stream_previous_scene])
                if response is not False:
                    self.stream_previous_scene = 'pause'
            else:
                response = self.set_scene(self.scene_dict['pause'])
                if response is not False:
                    self.stream_previous_scene = scene
        return response

    # -> pause
    @obs_is_running
    @obs_is_streaming
    def scene_set_pause_on(self):
        response = False
        scene = self._get_scene_id(self.obs_monitor.scene_name)
        if not scene in ['intro', 'pause'] :
            response = self.set_scene(self.scene_dict['pause'])
            if response is not False:
                self.stream_previous_scene = scene
        return response

    # <- pause
    @obs_is_running
    @obs_is_streaming
    def scene_set_pause_off(self):
        response = False
        scene = self._get_scene_id(self.obs_monitor.scene_name)
        if scene == 'pause' :
            response = self.set_scene(self.scene_dict[self.stream_previous_scene])
            if response is not False:
                self.stream_previous_scene = 'pause'
        return response


    # auto scene swich by bw_in
    def scene_switch_by_bitrate(self, bitrate: int, avg_bitrate: int):
        response = False
        scene = self._get_scene_id(self.obs_monitor.scene_name)
        if scene in ['intro', 'pause']:
            print('switch skipped')
            return response

        # live -> fail
        if avg_bitrate < self.fail_bw: # or bitrate <= 0 :
            response = self.scene_set_fail()

        # live -> live
        elif scene in ['live']:
            return response

        # fail, low -> live
        else:
            response = self.scene_set_live()
        return response
