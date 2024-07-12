import asyncio
import obswebsocket
from obswebsocket import obsws, requests, exceptions
from .logger import LoggerConfig

class OBSMonitor:
    def __init__(self, host='localhost', port=4455, password=''):
        self.host = host
        self.port = port
        self.password = password
        self.is_obs_running = False
        self.is_obs_streaming = False
        self.check_interval = 10
        self.logger = LoggerConfig.get_logger(self.__class__.__name__)
        self.ws = obsws(self.host, self.port, self.password)

    async def check_obs_status(self):
        try:
            self.logger.info('Trying to connect to OBS...')
            await asyncio.wait_for(asyncio.to_thread(self.ws.connect), timeout=5)
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
            if self.is_obs_running:
                self.logger.info("OBS is running.")
                self.check_interval = 30

            else:
                self.logger.warning("OBS is not running.")
                self.check_interval = 10

            await asyncio.sleep(self.check_interval)

    def run(self):
        async def start():
            while True:
                await self.monitor()
        asyncio.run(start())

if __name__ == "__main__":
    monitor = OBSMonitor()
    monitor.run()
