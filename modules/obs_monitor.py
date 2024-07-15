# -*- coding: utf-8 -*-
import asyncio
import threading
from obswebsocket import obsws, requests, exceptions
from .logger import LoggerConfig

class OBSMonitor:
    def __init__(self, host:str, port:int, password:str):
        self.is_obs_running = False
        self.is_obs_streaming = False
        self.check_interval = 10
        self.logger = LoggerConfig.get_logger(self.__class__.__name__)
        self.ws = obsws(host, port, password)

    async def check_obs_status(self):
        try:
            self.logger.info('Trying to connect to OBS...')
            await asyncio.wait_for(asyncio.to_thread(self.ws.connect), timeout=5)
            self.logger.info("OBS is running.")
            self.check_interval = 30
            # 配信状況確認
            status = self.ws.call(requests.GetStreamStatus())
            self.is_obs_streaming = status.getOutputActive()
            self.logger.info(f"Streaming status: {self.is_obs_streaming}")
            self.ws.disconnect()
            return True

        except (exceptions.ConnectionFailure, asyncio.TimeoutError):
            return False

    async def monitor(self):
        while True:
            self.is_obs_running = await self.check_obs_status()
            if not self.is_obs_running:
                self.logger.warning("OBS is not running.")
                self.check_interval = 10

            await asyncio.sleep(self.check_interval)

    def run(self):
        def _run():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(self.monitor())

        obs_monitoring_thread = threading.Thread(target=_run)
        obs_monitoring_thread.daemon = True
        obs_monitoring_thread.start()

def main():
    import time
    monitor = OBSMonitor(
        host="xxx.xxx.xxx.xxx",
        port=4455,
        password="your_obs_ws_pw"
    )
    monitor.run()
    while True:
        print('loop...')
        time.sleep(2)

if __name__ == "__main__":
    main()
