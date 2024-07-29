# RTMP-Monitoring-App
IRL配信のためのRTMPリレーサーバー監視アプリケーションです。  
OBSと連携し、シーンの切り替え等を行います。  

## Description

RTMPリレーサーバーへ送られた映像の受信ビットレートを監視しています。  
回線が悪くなると自動的に待機画面へ切り替え、復帰すると画面を戻します。  
twitchのチャットボットやdiscordボットと連携して、配信開始や終了、待機画面の表示を行うことができます。  
ビットレート値をhtmlソースでOBSへ取り込めます。

## Attention
動作確認は行っていますが、バグ等は残っていると思いますので、自己責任でお願いします。  

## Getting Started

### Dependencies
* Python 3.10.12
* リレーサーバーにnginxを使用します。
* applicationの名称はliveとしてください。  
  
```
conf:nginx.conf
rtmp_auto_push on;
rtmp {
    server {
        listen 1935;
        ping 3s;
        ping_timeout 15s;
        timeout 15s;
 
        application live {
            live on;
            record off;
        }
    }
}
```

### Installing

* config-sample.iniをconfig.iniに変更し、内容を自分の環境に合わせて修正してください
```
[obs]
;streamkeyの設定、なんでもよい
streamkey = your_rtmp_streamkey

;OBSのwebsocket関連の設定、自身の環境にあわせてください
OBS_WS_host = 192.168.xxx.xxx
OBS_WS_port = 4455
OBS_WS_Passwd = your_obs_ws_password

;各シーンの名称、必要に応じて変更するか、OBS側のシーン名を以下のようにしてください
Scene_Intro = Intro
Scene_Live  = Live
Scene_Fail  = Fail
Scene_Pause = Pause

;通信切断・低下時にFailに切り替えるビットレート値[bps]、kbpsではないです
RTMP_Fail_Bitrate = 500

[http]
;webhook関連の設定
webhook_port = 5000
webhook_path = /webhook
monitoring_utl = http://127.0.0.1/stat

;監視関係の設定、切り替え判定の間隔[sec]
monitoring_interval = 20

[twitch]
;twitchボットの設定
Connect = false
obs_command_control = false
Login_Channel = your_twitch_channel_name
Access_Token = bot_account_token
Command_Prefix = ?

[discord]
discordボットの設定
Connect = false
obs_command_control = false
;botが反応するチャンネルID、カンマ区切りで
Target_Channel_IDs = bot_monitoring_channel_id1,bot_monitoring_channel_id2,
Token = bot_account_token
Command_Prefix = ?
```

### Executing program
* appを起動します
```
python main.py
```

twitch、discordで使えるコマンドです(共通)
```
?stream start  OBSの配信開始、Intro画面です(準備画面)
?stream live   配信開始、カメラ配信の開始
?stream stop   配信終了、OBS配信終了
?stream pause  一時待機画面の切り替え、トグル式
?stream init   配信設定の初期化、配信中ではIntro画面になります。切り替えの調子が悪くなったり、配信終了後に

?pause         一時待機画面へ遷移
?pause on      一時待機画面へ遷移、上と同じ
?pause off     一時待機画面から復帰
```
**ボットを使用する際は、権限等に十分注意してください**  

* カメラのビットレートを配信画面に乗せるには  
付属ファイルのbitrate.html内29行目のurlをリレーサーバーに合わせて指定してください。
```
<script src="https://code.jquery.com/jquery-3.6.0.min.js"></script>
<script>
    $(document).ready(function() {
        function fetchBitrate() {
            $.getJSON('http://your_rtmp_svr:5000/avg_bitrate', function(data) {
                var kbps = (data.bitrate / 1000).toFixed(2);
                $('#bitrate').text(kbps + ' kbps');
            });
        }
        fetchBitrate();
        setInterval(fetchBitrate, 1000); // 1秒おきに取得
    });
</script>
```

OBSでhtmlソースを準備して、取り込んでください。  
こちらはサンプルですので、ご自由に改変したり、自由に作成してください。
  
## Help


## Authors


## Version History
* β1.1
    * obs_monitor周りを改修
    * 配信ステータスを取得するwebhookを追加
  
* β1.0
    * Initial Release

## License

This project is licensed under the MIT License - see the LICENSE.md file for details
