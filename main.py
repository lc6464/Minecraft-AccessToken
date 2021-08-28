from json import dump
from selenium import webdriver
from urllib.parse import urlparse, parse_qs
from requests import post, get


def getCode():
	driver = webdriver.Edge(executable_path=r'C:\Program Files (x86)\Microsoft\Edge\Application\msedgedriver.exe')
	driver.get('https://login.live.com/oauth20_authorize.srf?client_id=00000000402b5328' +  # Minecraft ID
		'&response_type=code&scope=service%3A%3Auser.auth.xboxlive.com%3A%3AMBI_SSL' +
		'&redirect_uri=https%3A%2F%2Flogin.live.com%2Foauth20_desktop.srf')  # 不能改
	result = urlparse(driver.current_url)  # 会被重定向，获取一下 URL
	driver.close()  # 关浏览器
	code = None
	if result.hostname == 'login.live.com' and result.path == '/oauth20_desktop.srf':
		query = parse_qs(result.query)
		if 'code' in query and 'lc' in query and 'error' not in query:
			code = query['code'][0]
	return code


def getToken(code):
	token = None
	result = post('https://login.live.com/oauth20_token.srf',
		{
			"client_id": "00000000402b5328",  # Minecraft ID
			"code": code,  # getCode
			"grant_type": "authorization_code",
			"redirect_uri": "https://login.live.com/oauth20_desktop.srf",
			"scope": "service::user.auth.xboxlive.com::MBI_SSL"
		})
	json = result.json()
	if result.status_code == 200 and 'access_token' in json and 'error' not in json:
		token = json['access_token']
	return token

def authXBL(accessToken):
	token = None
	uhs = None
	result = post('https://user.auth.xboxlive.com/user/authenticate',
		json = {
			"Properties": {
				"AuthMethod": "RPS",
				"SiteName": "user.auth.xboxlive.com",
				"RpsTicket": accessToken  # getToken
			},
			"RelyingParty": "http://auth.xboxlive.com",
			"TokenType": "JWT"
		})
	json = result.json()
	if result.status_code == 200 and 'Token' in json and 'DisplayClaims' in json and 'error' not in json:
		token = json['Token']
		uhs = json['DisplayClaims']['xui'][0]['uhs']
	return { 'Token': token, 'uhs': uhs }


def authXSTS(XBLToken, uhs):
	token = None
	newUhs = None
	result = post('https://xsts.auth.xboxlive.com/xsts/authorize',
		json = {
			"Properties": {
				"SandboxId": "RETAIL",
				"UserTokens": [ XBLToken ]  # authXBL
			},
			"RelyingParty": "rp://api.minecraftservices.com/",
			"TokenType": "JWT"
		})
	json = result.json()
	if result.status_code == 200 and 'Token' in json and 'DisplayClaims' in json and 'error' not in json:
		token = json['Token']
		newUhs = json['DisplayClaims']['xui'][0]['uhs']
		if uhs != newUhs:
			uhs = None
			token = None
	return { 'Token': token, 'uhs': uhs }

def getAccessToken(token, uhs):
	result = post('https://api.minecraftservices.com/authentication/login_with_xbox',
		json = {
			"identityToken": "XBL3.0 x=%s;%s" % (uhs, token)
		})
	accessToken = None
	json = result.json()
	if result.status_code == 200 and 'access_token' in json and 'error' not in json:
		accessToken = json['access_token']
	return accessToken

def checkHaveGame(accessToken):
	result = get('https://api.minecraftservices.com/entitlements/mcstore',
		headers={
			'Authorization': 'Bearer %s' % accessToken
		})
	isHave = None
	json = result.json()
	if result.status_code == 200 and 'items' in json and 'error' not in json:
		isHave = True if len(json['items']) != 0 else False
	return isHave

def getInfo(accessToken):
	result = get('https://api.minecraftservices.com/minecraft/profile',
		headers={
			'Authorization': 'Bearer %s' % accessToken
		})
	uuid = None
	name = None
	json = result.json()
	if result.status_code == 200 and 'id' in json and 'name' in json and 'error' not in json:
		uuid = json['id']
		name = json['name']
	return { 'UUID': uuid, 'name': name }


if __name__ == '__main__':
	print('1/5\t正在获取 Microsoft 验证代码……\n请在打开的浏览器窗口中登录您的 Microsoft 账户！')
	code = getCode()
	if code != None:
		print('2/5\t正在获取 Microsoft 验证令牌……')
		token = getToken(code)
		if token != None:
			print('3/5\t正在获取 Xbox Live 令牌……')
			xbl = authXBL(token)
			if xbl['Token'] != None:
				print('4/5\t正在获取 XSTS 令牌……')
				xsts = authXSTS(xbl['Token'], xbl['uhs'])
				if xsts['Token'] != None:
					print('5/5\t正在获取 Minecraft Access Token……')
					accessToken = getAccessToken(xsts['Token'], xsts['uhs'])
					if accessToken != None:
						output = { 'AccessToken': accessToken }
						print('\n您的 Minecraft Access Token 为：%s' % accessToken)
						isCheck = input('\n输入 y 以检查您的账户是否含有 Minecraft: Java Edition ，若有则一并获取游戏名和 UUID.')
						if isCheck in ['y', 'Y', 'yes', 'Yes', 'YES']:
							isHave = checkHaveGame(accessToken)
							if isHave == None:
								output['isHaveGame'] = 'Unknow'
								print('获取账户信息失败！')
							elif isHave:
								output['isHaveGame'] = isHave
								info = getInfo(accessToken)
								if info['UUID'] != None:
									output['name'] = info['name']
									output['UUID'] = info['UUID']
									print('\n游戏名：%s\nUUID：%s' % (info['name'], info['UUID']))
								else:
									output['name'] = None
									output['UUID'] = 'Unknow'
									print('获取游戏名及 UUID 失败！')
							else:
								output['isHaveGame'] = isHave
								print('您的帐户中没有 Minecraft: Java Edition！\n您可以访问 Minecraft 官网以购买！')
						else:
							output['isHaveGame'] = 'NoCheck'
						with open('minecraft_accessToken.json', 'wt', encoding='utf-8') as f:
							dump(output, f, ensure_ascii=False, indent=4)
							f.close()
						with open('accessToken.txt', 'wt', encoding='utf-8') as f:
							f.write(accessToken)
							f.close()
					else:
						print('获取 Minecraft Access Token 失败！')
				else:
					print('获取 XSTS 令牌失败！')
			else:
				print('获取 Xbox Live 令牌失败！')
		else:
			print('获取 Microsoft 验证令牌失败！')
	else:
		print('获取 Microsoft 验证代码失败！')