# -*- coding: utf-8 -*-
import asyncio
import aiohttp
import threading
import xml.etree.ElementTree as ET
from collections import deque

class RTMPMonitor:
    def __init__(self, rtmp_stat_url: str, streamkey: str, monitoring_interval: float = 0.5, sec_of_average_bitrate: float = 30):
        self.rtmp_stat_url = rtmp_stat_url
        self.streamkey = streamkey
        self.interval = monitoring_interval
        maxlen = int(round(sec_of_average_bitrate/monitoring_interval))
        self.bw_in_values = deque(maxlen=maxlen)
        self.bw_in = 0 #最新値
        self.avg_bw_in = 0 #平均値

    async def fetch_rtmp_stats(self):
        async with aiohttp.ClientSession() as session:
            async with session.get(self.rtmp_stat_url) as response:
                if response.status == 200:
                    return await response.text()
                else:
                    return None

    def parse_bw_in(self, xml_data: str):
        root = ET.fromstring(xml_data)
        nclients = int(root.findtext("server/application[name='live']/live/nclients"))
        if nclients == 0:
            return None
        bw_in = int(root.findtext(f"server/application/[name='live']/live/stream[name='{self.streamkey}']/bw_in"))
        return bw_in

    def calculate_average_bw_in(self):
        if len(self.bw_in_values) == 0:
            return 0
        return sum(self.bw_in_values) / len(self.bw_in_values)

    async def monitor(self):
        while True:
            xml_data = await self.fetch_rtmp_stats()
            if xml_data:
                self.parse_bw_in(xml_data)
                bw_in = self.parse_bw_in(xml_data)
                if bw_in is not None:
                    self.bw_in = round(bw_in, 1)
                    self.bw_in_values.append(bw_in)
                    self.avg_bw_in = round(self.calculate_average_bw_in(), 1)
                else:
                    self.bw_in = 0
            await asyncio.sleep(self.interval)

    def run(self):
        print("start rtmp monitoring")
        def _run():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(self.monitor())

        rtmp_monitoring_thread = threading.Thread(target=_run)
        rtmp_monitoring_thread.daemon = True
        rtmp_monitoring_thread.start()


def main():
    import time
    rtmp_monitor = RTMPMonitor(
        rtmp_stat_url='http://localhost/stat',
        streamkey='your_key'
    )
    rtmp_monitor.run()
    while True:
        print('loop...')
        time.sleep(2)

if __name__ == "__main__":
    main()
