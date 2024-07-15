# -*- coding: utf-8 -*-
import discord
from discord.ext import commands
import requests
# from modules.scheduler import Scheduler
from modules.logger import LoggerConfig

def discord_bot(config_ini):
    intents = discord.Intents.default()
    intents.message_content = True
    bot = commands.Bot(
        command_prefix=config_ini['discord']['Command_Prefix'],
        intents=intents
    )
    is_command_control = config_ini.getboolean('discord', 'obs_command_control')
    tgt_channel_ids = [int(id) for id in config_ini['discord']['Target_Channel_IDs'].split(',') if id.strip()]
    webhook_url = 'http://localhost:' + config_ini['http']['webhook_port'] + config_ini['http']['webhook_path']

    # scheduler = Scheduler()
    logger = LoggerConfig.get_logger(discord_bot.__name__)
    logger.info('discord bot init')

    @bot.event
    async def on_ready():
        print(f'Logged on as {bot.user}!')

    @bot.event
    async def on_message(message):
        if message.author == bot.user:
            return
        await bot.process_commands(message)

    def _is_in_target_channel(ctx):
        return ctx.channel.id in tgt_channel_ids

    @bot.command(name='hello')
    async def hello(ctx):
        if not _is_in_target_channel(ctx):
            return
        await ctx.reply('Hello!')

    @bot.command(name='stream')
    async def stream(ctx, args: str):
        if not _is_in_target_channel(ctx):
            return
        if not is_command_control:
            return

        response = await _handle_stream_command(args)
        await _process_response(ctx, response)

    @bot.command(name='pause')
    async def pause(ctx, args: str = None):
        if not _is_in_target_channel(ctx):
            return
        if not is_command_control:
            return

        response = await _handle_pause_command(args)
        await _process_response(ctx, response)

    async def _handle_stream_command(command: str):
        valid_commands = {
            'start': 'start',
            'on': 'start',
            'stop': 'stop',
            'end': 'stop',
            'off': 'stop',
            'live': 'live',
            'pause': 'pause',
            'init': 'init',
        }

        if command in valid_commands:
            return _post_to_webhook({'stream': valid_commands[command]}, webhook_url)
        return None

    async def _handle_pause_command(command: str):
        if command == 'on' or command is None:
            return _post_to_webhook({'pause': 'on'}, webhook_url)
        elif command == 'off':
            return _post_to_webhook({'pause': 'off'}, webhook_url)
        return None

    async def _process_response(ctx, response):
        if response is None:
            await ctx.send('incorrect argument!')
            return

        if response.status_code == 200:
            message = {
                'start': '配信準備中',
                'stop': '配信終了',
                'live': '配信開始',
                'pause': '待機を切り替えます',
                'init': '初期化します'
            }.get(response.json().get('stream'), '操作完了')
            await ctx.send(message)
        else:
            await ctx.send('コマンドの実行に失敗しました')

    @bot.event
    async def on_command_error(ctx, error):
        if isinstance(error, commands.CommandNotFound):
            await ctx.send('コマンドがありません')
        elif isinstance(error, commands.MissingRequiredArgument):
            await ctx.send('コマンドの引数が間違っています')
        else:
            await ctx.send(f'コマンドエラーです: {error}')

    def _post_to_webhook(data: dict, url: str) -> bool:
        try:
            response = requests.post(url, json=data)
            response.raise_for_status()

        except requests.RequestException as e:
            print(f"Failed to send POST request: {e}")

        finally:
            return response

    return bot
