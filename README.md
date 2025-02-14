# ILSH Sandwatch V1.0

## 社区支持
- 💬 官方：[空投信息、脚本TG频道](https://t.me/ilsh_auto)
- 🐦 最新公告：[我们的推特](https://x.com/hashlmBrian)

## ⚠️ 重要安全警告

**涉及敏感信息操作须知：**

1. 本系统需处理钱包助记词等敏感信息
2. **必须**在可信的本地环境运行
3. 禁止将助记词上传至任何网络服务

## 🚀 快速开始

本代码分js、python两部分。
js：用于sol链签名
python：用于与sandwatch服务端交互

### JavaScript 环境配置
建议使用 Webstorm、HBuilder等专业工具。出现问题请使用deepseek、chatGPT、Claude

安装Node.js环境（需14.x以上版本）

curl -fsSL https://deb.nodesource.com/setup_16.x | sudo -E bash -
sudo apt-get install -y nodejs
安装项目依赖
````
cd js
npm init -y
npm install express body-parser ethers @solana/web3.js bip39 bs58 socks-proxy-agent ed25519-hd-key node-fetch@2
tweetnacl
启动签名服务
node js_server.js
````

### Python 环境配置


```` 
安装Python依赖
pip install -r requirements.txt --user
准备账户配置文件
"助记词----代理地址"
示例配置内容：
angry list clock vacuum dizzy phrase... ---- socks5://user:pass@127.0.0.1:1080
运行主程序
python sandwatch.py
````

## 免责声明

本工具仅用于区块链技术研究，使用者应自行承担以下风险：

1. 本地环境安全导致的资产损失
2. 自动化操作触发的风控机制
3. 网络延迟造成的交易失败
4. 其他不可预见的链上风险