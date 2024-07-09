# -*- coding: utf-8 -*-
import configparser
import multiprocessing as mp
import twitch_bot
from discord_bot import discord_bot
from web_app import WebApp
from logger_module import LoggerConfig

def run_twitch(config_ini, stream_status):
    twitch = twitch_bot.create(config_ini, stream_status)
    twitch.run()

def run_discord(config_ini, stream_status):
    discord = discord_bot(config_ini, stream_status)
    discord.run(config_ini['discord']['Token'])

def main():
    try:
        logger = LoggerConfig.get_logger('main')
        config_ini = configparser.ConfigParser()
        config_ini.read('config.ini', encoding='utf-8')

        is_connect_twich   = config_ini.getboolean('twitch', 'Connect')
        is_connect_discord = config_ini.getboolean('discord', 'Connect')

        manager = mp.Manager()
        stream_status = manager.dict()
        stream_status['stream_camera_on'] = False
        stream_status['stream_scene'] = 'intro' # [intro, live, fail, low]
        stream_status['stream_previous_scene'] = 'intro'
        stream_status['stream_bitrate'] = None
        stream_status['obs_active'] = False

        p_twitch  = None
        p_discord = None

        if is_connect_twich:
            logger.info('startup twitch bot process')
            p_twitch =mp.Process(
                target=run_twitch, args=(config_ini, stream_status) )
            p_twitch.start()

        if is_connect_discord:
            logger.info('startup discord bot process')
            p_discord =mp.Process(
                target=run_discord, args=(config_ini, stream_status) )
            p_discord.start()

        web_app = WebApp(config_ini, stream_status)
        web_app.run()


    except (KeyboardInterrupt, SystemExit):  # Ctrl+Cが押されたときに発生する例外をキャッチする
        logger.info('Ctrl+C detected, stopping workers...')
        del web_app
        if is_connect_twich:
            p_twitch.terminate()
            p_twitch.join()

        if is_connect_discord:
            p_discord.terminate()
            p_discord.join()

if __name__ == "__main__":
    main()
