# Minecraft-AccessToken
### 获取微软账户的 Minecraft Access Token.

原理可在 [wiki.vg](https://wiki.vg/ZH:Microsoft_Authentication_Scheme "wiki.vg 中的页面") 中查询。

由于第一步骤：Microsoft 账户登录需要使用到浏览器，而此程序的解决方法是用 `selenium` 的 `Microsoft Edge webdriver`，请准备好相关程序。<br/>
可在[此处](https://developer.microsoft.com/zh-cn/microsoft-edge/tools/webdriver/ "Microsoft 官方网站中的页面")下载，并在 `main.py` 中自行将文件路径改为你的。<br/>
另外就是设备上肯定得有 Microsoft Edge 才行。

如果你使用 Chrome 或 Firefox 等其他的浏览器，请自行修改 `driver` 和程序。