import asyncio
import obswebsocket
from obswebsocket import obsws, requests, exceptions

class OBSMonitor:
    def __init__(self, host='localhost', port=4444, password=''):
        self.host = host
        self.port = port
        self.password = password
        self.is_running = False
        self.check_interval = 10  # 初期確認間隔は10秒

    async def check_obs_running(self):
        try:
            ws = obsws(self.host, self.port, self.password)
            ws.connect()
            ws.disconnect()
            return True
        except exceptions.ConnectionFailure:
            return False

    async def monitor(self):
        while True:
            self.is_running = await self.check_obs_running()
            if self.is_running:
                print("OBS is running.")
                self.check_interval = 60  # 起動確認後は1分間隔
            else:
                print("OBS is not running.")
                self.check_interval = 10  # 起動確認が取れなくなったら10秒間隔

            await asyncio.sleep(self.check_interval)

    async def run(self):
        while True:
            await self.monitor()

if __name__ == "__main__":
    monitor = OBSMonitor()
    asyncio.run(monitor.run())
