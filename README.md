# RTMP-Monitoring-App
IRL配信のためのRTMPリレーサーバー監視アプリケーションです。  
OBSと連携し、シーンの切り替え等を行います。  
  **書きかけです**

RTMP relay server monitoring application for IRL streaming.  
It works with OBS to perform scene switching, etc.  
*Using deepL for English translation  
  **This readme is in progress**

## Description

RTMPリレーサーバーへ送られた映像の受信ビットレートを監視しています。  
受信の値が悪くなると自動的に待機画面へ切り替え、値が回復すると復帰させます。  
twitchのチャットボットやdiscordボットと連携して、配信開始や終了、手動待機を行うことができます。  
ビットレート値をhtmlソースでOBSへ取り込めます。


Monitoring received bitrate of video sent to the RTMP relay server.  
When the value of reception bitrate becomes bad, the system automatically switches to the standby screen and restores it when the value recovers.  
It can work with twitch chatbots and discord bots to start, end, and standby manually for live streaming.  
Bitrate values can be imported into OBS via html source.  

## Attention
動作確認は行っていますが、バグ等は残っていると思いますので、自己責任でお願いします。  
Checked the operation, but I believe there are still bugs, etc. Please do so at your own risk.  

## Getting Started

### Dependencies
* Python 3.10.12
  
* リレーサーバーにnginxを使用します。
* applicationの名称はliveとしてください。  
  
* Use nginx as relay server.
* Name of the application should be "live".
  
```conf:nginx.conf
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

* 自分の環境に合わせて、config.iniを編集してください
* Edit config.ini to suit your PC settings.

### Executing program

```
python main.py
```

## Help


## Authors


## Version History

* β1.0
    * Initial Release

## License

This project is licensed under the MIT License - see the LICENSE.md file for details
