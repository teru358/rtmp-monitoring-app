# -*- coding: utf-8 -*-
from flask import Flask, request, jsonify, make_response
from flask_cors import CORS
from obs_operator import OBSOperator
from modules.rtmp_monitor import RTMPMonitor
from modules.scheduler import Scheduler
from modules.logger import LoggerConfig

class WebApp:
    def __init__(self, config_ini):
        self.webhook_port = config_ini['http']['webhook_port']
        self.webhook_path = config_ini['http']['webhook_path']
        self.monitoring_interval = int(config_ini['http']['monitoring_interval'])

        self.app = Flask(__name__)
        CORS(self.app)
        self.obs_operator = OBSOperator(config_ini)
        self.rtmp_monitor = RTMPMonitor(
            rtmp_stat_url=config_ini['http']['monitoring_utl'],
            streamkey=config_ini['obs']['streamkey'],
            monitoring_interval_sec=0.5, # rtmp_statを監視する間隔、
            average_bitrate_sec=5 # 平均ビットレートを計算する秒数、長すぎると自動切替等に影響
        )
        self.scheduler = Scheduler()
        self.logger = LoggerConfig.get_logger(self.__class__.__name__)

        self._setup_routes()
        self._setup_scheduler()
        self.rtmp_monitor.run()

        self.logger.info('Started Web App!')

    # webhookによる切替操作
    def _setup_routes(self):
        @self.app.route(self.webhook_path, methods=['POST'])
        def webhook():
            data = request.json
            response = None
            if "stream" in data:
                response = self._handle_stream_action(data.get("stream"), data)
            elif "pause" in data:
                response = self._handle_pause_action(data.get("pause"))

            if response:
                return self._create_response(data, success=True)
            else:
                return self._create_response(data, success=False)

        @self.app.route('/bitrate', methods=['GET'])
        def bitrate():
            res = make_response(jsonify({'bitrate': str(self.rtmp_monitor.bw_in)}), 200)
            res.headers['Content-Type'] = 'application/json'
            return res

        @self.app.route('/avg_bitrate', methods=['GET'])
        def avg_bitrate():
            res = make_response(jsonify({'bitrate': str(self.rtmp_monitor.avg_bw_in)}), 200)
            res.headers['Content-Type'] = 'application/json'
            return res


    def _handle_stream_action(self, action, data):
        stream_actions = {
            "start": self.obs_operator.stream_start,
            "stop": self.obs_operator.stream_stop,
            "live": self.obs_operator.stream_to_live,
            "pause": self.obs_operator.scene_switch_pause,
            "text": lambda: self.obs_operator.set_text_source('bitrate', data['content']),
            "init": self.obs_operator.stream_initialize,
        }
        return stream_actions.get(action)()

    def _handle_pause_action(self, action):
        pause_actions = {
            "on": self.obs_operator.scene_set_pause_on,
            "off": self.obs_operator.scene_set_pause_off,
        }
        return pause_actions.get(action)()

    def _create_response(self, data, success=True):
        status = 'success' if success else 'error'
        status_code = 200 if success else 400
        response_data = {**data, 'status': status}

        res = make_response(jsonify(response_data), status_code)
        res.headers['Content-Type'] = 'application/json'
        return res

    def _setup_scheduler(self):
        self.scheduler.add_interval_job_condition(
            func=self._stream_scene_control,
            condition_func=self._check_stream_status,
            seconds=self.monitoring_interval,
            job_id="scene_control",
        )

    def _check_stream_status(self):
        if self.obs_operator.obs_monitor.is_obs_streaming:
            if not self.obs_operator.stream_scene in ['intro', 'pause']:
                return True
        return False

    # bitrate監視によるシーン切り替え
    def _stream_scene_control(self):
        self.obs_operator.scene_switch_by_bitrate(
            bitrate=self.rtmp_monitor.bw_in,
            avg_bitrate=self.rtmp_monitor.avg_bw_in
        )

    def run(self):
        self.app.run(
            host='0.0.0.0',
            port=self.webhook_port
        )

# ファイルが直接実行されたときだけサーバーを起動
if __name__ == '__main__':
    web_app = WebApp()
    web_app.run()
