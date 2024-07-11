# -*- coding: utf-8 -*-
from flask import Flask, request, jsonify
import requests
import xml.etree.ElementTree as ET
from obs_operator import OBSOperator
from modules.scheduler import Scheduler
from modules.logger import LoggerConfig

class WebApp:
    def __init__(self, config_ini, stream_status):
        self.config_http = config_ini['http']
        self.config_obs  = config_ini['obs']
        self.stream_status = stream_status

        self.app = Flask(__name__)
        self.obs_operator = OBSOperator(config_ini, stream_status)
        self.scheduler = Scheduler()
        self.logger = LoggerConfig.get_logger(self.__class__.__name__)
        self._setup_routes()
        self._setup_scheduler()
        self.obs_operator.start_monitoring()

        self.logger.info('Started Web App!')

    # webhookによる手動切替操作
    def _setup_routes(self):
        @self.app.route(self.config_http['webhook_path'], methods=['POST'])
        def webhook():
            data = request.json
            # Webhookで受信したデータを処理する
            if ('stream', 'start') in data.items(): # 配信開始
                self.obs_operator.stream_start()

            elif ('stream', 'stop') in data.items(): # 配信終了
                self.obs_operator.stream_stop()

            elif ('stream', 'restart') in data.items(): # 配信再起動
                pass

            elif ('stream', 'live') in data.items(): # live画面へ(カメラONしたあと)
                bw_in = self._get_bw_in()
                if int(self.config_obs['RTMP_Low_Bitrate_Value']) < bw_in :
                    self.obs_operator.stream_to_live()

            elif ('stream', 'pause') in data.items(): # pause画面
                self.obs_operator.stream_switching_pause()

            elif ('stream', 'text') in data.items():
                self.obs_operator.set_text_source('bitrate', data['content'])

            return jsonify({'status': 'success'})

    def _setup_scheduler(self):
        self.scheduler.add_interval_job_condition(
            func=self._stream_status_control_monitoring,
            condition_func=self._scene_auto_switch_permission,
            seconds=int(self.config_http['monitoring_interval']),
            job_id="stream_control",
        )
        if self._scene_auto_switch_permission():
            self._stream_status_control_monitoring()

        # self.scheduler.add_interval_job(
        #     func=self._obs_alive_monitoring,
        #     seconds=20,
        #     job_id="_obs_alive_monitoring",
        # )
        # self._obs_alive_monitoring()

    # OBS 死活監視 要検討
    # def _obs_alive_monitoring(self):
    #     streamkey = self.config_obs["streamkey"]
    #     obs_active = self._get_rtmp_stat_xml(f".//stream[name='{streamkey}']")
    #     if obs_active is not None:
    #         self.stream_status['obs_active'] = True
    #     else:
    #         self.stream_status['obs_active'] = False

    # 配信状態の監視
    # カメラが生きてる and シーンがintroではない and 配信中
    def _scene_auto_switch_permission(self):
        return ( not self.stream_status['stream_camera_on'] and
            not self.stream_status['stream_scene'] == 'intro' and
            self.obs_operator.is_streaming_true()
        )

    # bw_inによる自動切替操作、スケジューラーによる監視
    def _stream_status_control_monitoring(self):
        if self.stream_status['stream_scene'] in ['intro', 'pause']:
            print('switch skipped')
            return
        bw_in = self._get_bw_in()
        self.logger.info(f'IRL bitrate {bw_in}')

        # bw_inが限界値以下ならfail画面へ遷移
        if bw_in <= int(self.config_obs['RTMP_Fail_Bitrate_Value']):
            self.obs_operator.scene_change_fail()

        # bw_inが既定値以下なら、ビットレート低下のソース表示、有効なら
        elif (bw_in <= int(self.config_obs['RTMP_Low_Bitrate_Value']) ) and self.config_obs.getboolean('RTMP_Low_Bitrate_Source_On'):
            self.obs_operator.source_swich_low_bitrate()

        # 問題なければ、liveに戻す
        else:
            if not (self.stream_status['stream_scene'] == 'live'):
                self.obs_operator.scene_change_live()

    def _get_bw_in(self):
        streamkey = self.config_obs['streamkey']
        bw_in = self._get_rtmp_stat_xml(f".//application[name='live']/live/stream[name='{streamkey}']/bw_in")
        bw_in = int(bw_in.text)
        return bw_in

    def _get_rtmp_stat_xml(self, param):
        response = requests.get(self.config_http['monitoring_utl'])
        if response.status_code == 200:
            xml_content = response.content
            root = ET.fromstring(xml_content)
            element = root.find(param)
            return element
        else:
            self.logger.warning(f"Failed to fetch XML. Status code: {response.status_code}")
            return None

    def run(self):
        self.app.run(host='0.0.0.0', port=self.config_http['webhook_port'])

# ファイルが直接実行されたときだけサーバーを起動
if __name__ == '__main__':
    web_app = WebApp()
    web_app.run()
