# -*- coding: utf-8 -*-
import asyncio
import threading
from obswebsocket import obsws, requests, exceptions
from .logger import LoggerConfig

class OBSMonitor:
    def __init__(self, host:str, port:int, password:str):
        self.is_obs_running = False
        self.is_obs_streaming = False
        self.scene_name = None
        self.logger = LoggerConfig.get_logger(self.__class__.__name__)
        self.ws = obsws(host, port, password, on_connect=self.on_connect, on_disconnect=self.on_disconnect)

    def on_connect(self, obs):
        self.is_obs_running = True
        self.logger.info("Connected to OBS")

    def on_disconnect(self, obs):
        self._condition_init()
        self.logger.info("Disconnected from OBS")

    def _condition_init(self):
        self.is_obs_running = False
        self.is_obs_streaming = False
        self.scene_name = None

    async def check_obs_running(self):
        while True:
            if not self.is_obs_running:
                try:
                    self.logger.info('Trying to connect to OBS...')
                    await asyncio.wait_for(
                        asyncio.to_thread(self.ws.connect),
                        timeout=5
                    )
                except (exceptions.ConnectionFailure, asyncio.TimeoutError):
                    self._condition_init()
            await asyncio.sleep(10)

    async def _update_stream_status(self):
        try:
            res = self.ws.call(requests.GetStreamStatus())
            if res.status:
                self.is_obs_streaming = res.getOutputActive()
            res = self.ws.call(requests.GetCurrentProgramScene())
            if res.status:
                self.scene_name = res.getSceneName()
        except exceptions.ConnectionFailure:
            self.logger.warning("Failed to check streaming status")

    async def check_obs_streaming(self):
        while True:
            if self.is_obs_running:
                await self._update_stream_status()
            await asyncio.sleep(2)

    async def _attempt_reconnection(self):
        try:
            self.logger.info('Trying to reconnect to OBS...')
            await asyncio.wait_for(
                asyncio.to_thread(self.ws.reconnect),
                timeout=5
            )
        except (exceptions.ConnectionFailure, asyncio.TimeoutError):
            self.reset_conditions()

    async def reconnection(self):
        while True:
            await asyncio.sleep(600)
            if self.is_obs_running:
                await self._attempt_reconnection()

    async def monitor(self):
        await asyncio.gather(
            self.check_obs_running(),
            self.check_obs_streaming(),
            self.reconnection()
        )

    def run(self):
        self.logger.info("start obs monitoring")
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
