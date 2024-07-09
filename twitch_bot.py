# -*- coding: utf-8 -*-
from twitchio import Channel, Message
from twitchio.ext import commands
import requests
import json
from obs_operator import OBSOperator
from scheduler_module import Scheduler
from logger_module import LoggerConfig

class TwitchBot(commands.Bot):

    def __init__(self, config_ini, stream_status):
        super().__init__(
            initial_channels=[config_ini['twitch']['Login_Channel']],
            token=config_ini['twitch']['Access_Token'],
            prefix=config_ini['twitch']['Command_Prefix'],
        )
        self.config_ini = config_ini
        self.stream_status = stream_status
        self.config = config_ini['twitch']
        self.obs_operator = OBSOperator(config_ini, stream_status)

        self.__auth_error_message = "権限がありません"
        self.__command_error_message = "コマンドを確認してください"
        self.scheduler = Scheduler()
        self.logger    = LoggerConfig.get_logger(self.__class__.__name__)
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
        # ボットの発言は無視する
        # if message.echo:
        #     return

        # メッセージがコマンドであれば、ここで処理を終了
        # if message.content.startswith(prefix):
        if message.echo or any(message.content.startswith(prefix) for prefix in ['!']):
            return

        user_name = message.author.name
        user_id = message.author.id
        print("{0}({1}): {2}".format(user_name, user_id, message.content))

        if message.content.startswith(self.config['Command_Prefix']):
            await self.handle_commands(message)

    # hello こんにちは
    @commands.command(name='hello')
    async def cmd_hello(self, ctx: commands.Context):
        await ctx.send(f'Hello! {ctx.author.name}!')

    '''
    # sample command
    @commands.cooldown(rate=1, per=60, bucket=commands.Bucket.user)
    @commands.command(name='sample')
    async def sample(self, ctx: commands.Context, args=None):
        if isinstance(args, str):
            if self.message_auth_check(ctx.message, ['broadcaster', 'moderator', 'vip', 'subscriber', 'all']):
                # do something
                pass
            else:
                await ctx.send(self.__auth_error_message)
        else:
            await ctx.send(self.__command_error_message)
    '''

    # sample command
    # @commands.cooldown(rate=1, per=60, bucket=commands.Bucket.user)
    @commands.command(name='stream')
    async def stream(self, ctx: commands.Context, args=None):
        if not config['obs_command_control'] :
            return
        if isinstance(args, str):
            if self.message_auth_check(ctx.message, ['broadcaster']):
                if args == "start":
                    # 配信開始送信
                    self.obs_operator.stream_start()
                    await ctx.send('stream start')
                elif args == "stop":
                    # 配信終了送信
                    self.obs_operator.stream_stop()
                    await ctx.send('stream end')
                else:
                    await ctx.send(self.__command_error_message)
            else:
                await ctx.send(self.__auth_error_message)
        else:
            await ctx.send(self.__command_error_message)

    # sample command
    # @commands.cooldown(rate=1, per=60, bucket=commands.Bucket.user)
    @commands.command(name='pause')
    async def pause(self, ctx: commands.Context, args=None):
        if not config['obs_command_control'] :
            return
        if isinstance(args, str):
            if self.message_auth_check(ctx.message, ['broadcaster']):
                # 一時中断送信
                self.obs_operator.stream_switching_pause()
                await ctx.send('stream pause')
            else:
                await ctx.send(self.__auth_error_message)
        else:
            await ctx.send(self.__command_error_message)

    def message_auth_check(self, message, auth_list):
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

def create(config, stream_status):
    return TwitchBot(config, stream_status)
