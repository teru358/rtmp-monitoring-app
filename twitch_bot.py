# -*- coding: utf-8 -*-
from twitchio import Channel, Message
from twitchio.ext import commands
import requests
import json
from modules.scheduler import Scheduler
from modules.logger import LoggerConfig

class TwitchBot(commands.Bot):

    def __init__(self, config_ini):
        super().__init__(
            initial_channels=[config_ini['twitch']['Login_Channel']],
            token=config_ini['twitch']['Access_Token'],
            prefix=config_ini['twitch']['Command_Prefix'],
        )
        self.prefix = config_ini['twitch']['Command_Prefix']
        self.is_command_control = config_ini.getboolean('twitch', 'obs_command_control')
        self.webhook_url = 'http://localhost:' + config_ini['http']['webhook_port'] + config_ini['http']['webhook_path']

        self.__auth_error_message = "権限がありません"
        self.__command_error_message = "コマンドを確認してください"
        self.scheduler = Scheduler()
        self.logger = LoggerConfig.get_logger(self.__class__.__name__)
        self.logger.info('twitch bot init')

    async def event_channel_joined(self, channel: Channel):
        print(f"ログインしました。チャンネル名: {channel.name}")
        for chatter in channel.chatters:
            print(f'ユーザーID: {chatter.id}')
            print(f'ユーザー名: {chatter.name}')
            print(f'表示名: {chatter.display_name}')
        await channel.send(f"{chatter.name} Logged in")

    async def event_ready(self):
        self.logger.info('started twitch bot!')

    # コメントが書き込まれると呼び出される
    async def event_message(self, message: Message):
        if message.echo or any(message.content.startswith(any_prefix) for any_prefix in ['!']):
            return

        user_name = message.author.name
        user_id = message.author.id
        print("{0}({1}): {2}".format(user_name, user_id, message.content))

        if message.content.startswith(self.prefix):
            await self.handle_commands(message)

    # hello こんにちは
    @commands.command(name='hello')
    async def cmd_hello(self, ctx: commands.Context):
        await ctx.send(f'Hello! {ctx.author.name}!')

    @commands.command(name='stream')
    async def stream(self, ctx: commands.Context, args=None):
        if not self.is_command_control:
            return

        if not isinstance(args, str):
            await ctx.send(self.__command_error_message)
            return

        if not self._message_auth_check(ctx.message, ['broadcaster']):
            await ctx.send(self.__auth_error_message)
            return

        response = await self._handle_stream_command(args)
        await self._process_response(ctx, response)

    @commands.command(name='pause')
    async def pause(self, ctx: commands.Context, args=None):
        if not self.is_command_control:
            return

        # if not isinstance(args, str):
        #     await ctx.send(self.__command_error_message)
        #     return

        if not self._message_auth_check(ctx.message, ['broadcaster']):
            await ctx.send(self.__auth_error_message)
            return

        response = await self._handle_pause_command(args)
        await self._process_response(ctx, response)

    async def _handle_stream_command(self, command: str):
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
            return self._post_to_webhook({'stream': valid_commands[command]}, self.webhook_url)
        return None

    async def _handle_pause_command(self, command: str):
        if command == 'on' or command is None:
            return self._post_to_webhook({'pause': 'on'}, self.webhook_url)
        elif command == 'off':
            return self._post_to_webhook({'pause': 'off'}, self.webhook_url)
        return None

    async def _process_response(self, ctx, response):
        if response is None:
            await ctx.send('incorrect argument!')
            return

        if response.status_code == 200:
            message = {
                'start': '配信準備中',
                'stop': '配信終了',
                'live': '配信開始',
                'pause': '待機を切り替えます'
            }.get(response.json().get('stream'), '操作完了')
            await ctx.send(message)
        else:
            await ctx.send('コマンドの実行に失敗しました')

    def _message_auth_check(self, message, auth_list):
        # auth_list [broadcaster, moderator, vip, subscriber, all]
        for auth in auth_list:
            if auth == 'broadcaster':
                if message.author.is_broadcaster: return True
            elif auth == 'moderator':
                if message.author.is_mod: return True
            elif auth == 'vip':
                if message.author.is_vip: return True
            elif auth == 'subscriber':
                if message.author.is_subscriber: return True
            elif auth == 'all':
                return True
        return False

    def _post_to_webhook(self, data: dict, url: str) -> bool:
        try:
            response = requests.post(url, json=data)
            response.raise_for_status()

        except requests.RequestException as e:
            print(f"Failed to send POST request: {e}")

        finally:
            return response

def create(config):
    return TwitchBot(config)
