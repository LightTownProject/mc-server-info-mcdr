# MC Server Info

*Simply get server info in [MCDReforged](https://github.com/Fallen-Breath/MCDReforged) and connect [NoneBot2](https://github.com/nonebot/nonebot2) to send data to QQ.*

在 [MCDReforged](https://github.com/Fallen-Breath/MCDReforged) 中获取简易的服务器信息，并连接 [NoneBot2](https://github.com/nonebot/nonebot2) 将数据发送到 QQ

## Installation

**TIP：本插件需要 Python 3.8+，目前仅适配了 MCDR 1.x，有关 2.x，请等待后续更新**

```bash
pip install -r requirements.txt
```

NoneBot2 端在[这里](https://github.com/LightTownProject/mc-server-info-bot)

然后复制 `mc_server_info.py` 到 `plugins` 目录下即可使用

## Config

修改 `mc_server_info.py` 下面几行

```python
# 服务器名称
SERVER_NAME: str = ""
# 服务器端口
PORT: int = 25565
# NoneBot2 服务器地址
WS_SERVER: str = "ws://127.0.0.1:8080/mcdr"
```

## Support

目前已支持/将要支持的功能

- [x] 获取服务器在线信息（版本，在线玩家数等）
- [ ] 崩溃检测
- [ ] 服务器占用统计
- [ ] 聊天
- [ ] 命令控制
- [ ] *More*

## License

本插件以 [AGPLv3](./LICENSE) 协议开源