# -*- coding: utf-8 -*-
from obs_websocket_module import OBSController

class OBSOperator(OBSController):

    def __init__(self, config, stream_status):
        self.config_obs = config['obs']
        self.stream_status = stream_status
        super().__init__(config['obs'])

    # 配信開始
    def stream_start(self):
        if not self.is_streaming():
            self.stream_status['stream_previous_scene'] = self.stream_status['stream_scene']
            self.stream_status['stream_scene'] = 'intro'
            self.set_source_in_scene_visibility(
                scene_name=self.config_obs['Scene_Live'],
                source_name=self.config_obs['RTMP_Low_Bitrate_Source_Name'],
                visibility='hidden'
            )
            self.set_scene(self.config_obs['Scene_Intro'])
            self.start_streaming()
            # self.logger.info('stream start!')

    # 配信終了（初期化）
    def stream_stop(self):
        if self.is_streaming():
            self.stop_streaming()
            if not self.get_streaming_status():
                self.set_source_in_scene_visibility(
                    scene_name=self.config_obs['Scene_Live'],
                    source_name=self.config_obs['RTMP_Low_Bitrate_Source_Name'],
                    visibility='hidden'
                )
                self.set_scene(self.config_obs['Scene_Intro'])
                self.stream_status['stream_previous_scene'] = self.stream_status['stream_scene']
                self.stream_status['stream_scene'] = 'intro'
            # self.logger.info('stream stop!')

    # introからliveへ（カメラON）
    def stream_to_live(self):
        self.set_scene(self.config_obs['Scene_Live'])
        self.stream_status['stream_previous_scene'] = self.stream_status['stream_scene']
        self.stream_status['stream_scene'] = 'live'
        self.stream_status['stream_camera_on'] = True

    # pause状態切替え(intro以外で)
    def stream_switching_pause(self):
        self.stream_status['stream_previous_scene'] = self.stream_status['stream_scene']
        if self.stream_status['stream_camera_on']:
            if self.stream_status['stream_scene'] == 'live':
                self.set_scene(self.config_obs['Scene_Live'])
            elif self.stream_status['stream_scene'] == 'fail':
                self.set_scene(self.config_obs['Scene_Fail'])
            self.stream_status['stream_camera_on'] = False
            # self.logger.info('stream unpaused!')
        else:
            self.set_scene(self.config_obs['Scene_Pause'])
            self.stream_status['stream_camera_on'] = True
            # self.logger.info('stream paused!')

    # sceneをintroにする
    def scene_change_intro(self):
        self.set_source_in_scene_visibility(
            scene_name=self.config_obs['Scene_Live'],
            source_name=self.config_obs['RTMP_Low_Bitrate_Source_Name'],
            visibility='hidden')
        self.set_scene(self.config_obs['Scene_Intro'])
        self.stream_status['stream_previous_scene'] = self.stream_status['stream_scene']
        self.stream_status['stream_scene'] = 'intro'

    # sceneをliveにする
    def scene_change_live(self):
        self.hide_source(
            scene_name=self.config_obs['Scene_Live'],
            source_name=self.config_obs['RTMP_Low_Bitrate_Source_Name'])
        self.set_scene(self.config_obs['Scene_Live'])
        self.stream_status['stream_previous_scene'] = self.stream_status['stream_scene']
        self.stream_status['stream_scene'] = 'live'
        self.stream_status['stream_camera_on'] = True
        # self.logger.info('scene change LIVE')

    # sceneをfailにする
    def scene_change_fail(self):
        self.set_scene(self.config_obs['Scene_Fail'])
        self.stream_status['stream_previous_scene'] = self.stream_status['stream_scene']
        self.stream_status['stream_scene'] = 'fail'
        # self.logger.info('scene change FAIL')

    # sceneをpauseに切り替える(intro以外で)
    def scene_switch_pause(self):
        if self.stream_status['stream_camera_on']:
            if self.stream_status['stream_scene'] == 'live':
                self.set_scene(self.config_obs['Scene_Live'])
            elif self.stream_status['stream_scene'] == 'fail':
                self.set_scene(self.config_obs['Scene_Fail'])
            self.stream_status['stream_camera_on'] = False
        else:
            self.set_scene(self.config_obs['Scene_Pause'])
            self.stream_status['stream_camera_on'] = True

    # sceneをpauseにする(intro以外で)
    def scene_change_pause_on(self):
        if not self.stream_status['stream_scene'] in ['intro', 'pause'] :
            self.set_scene(self.config_obs['Scene_Pause'])
            self.stream_status['stream_previous_scene'] = self.stream_status['stream_scene']
            self.stream_status['stream_scene'] = 'pause'
            # self.logger.info('scene change PAUSE')

    # sceneをpauseから戻す
    def scene_change_pause_off(self):
        if self.stream_status['stream_scene'] == 'pause' :
            self.set_scene(self.config_obs['stream_previous_scene'])
            self.stream_status['stream_scene'] = self.stream_status['stream_previous_scene']
            self.stream_status['stream_previous_scene'] = 'pause'
            # self.logger.info('scene change PAUSE')

    # source表示を切り替える
    def source_swich_low_bitrate(self):
        self.show_source(
            scene_name=self.config_obs['Scene_Live'],
            source_name=self.config_obs['RTMP_Low_Bitrate_Source_Name'])
        self.stream_status['stream_scene'] = 'low'
        # self.logger.info('source on bw_in LOW')
