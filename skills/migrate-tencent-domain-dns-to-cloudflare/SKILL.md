---
name: migrate-tencent-domain-dns-to-cloudflare
description: Safely migrate a Tencent Cloud or DNSPod-registered domain's authoritative DNS delegation to Cloudflare, including record inventory, Cloudflare zone onboarding, DNSSEC checks, registrar nameserver replacement, propagation verification, and failure diagnosis. Use when the user asks to move or switch a Tencent Cloud/DNSPod domain's DNS, nameservers, NS, or authoritative resolution to Cloudflare, whether they want guided instructions or direct browser operation.
---

# 腾讯云域名 DNS 迁移到 Cloudflare

将域名注册商处的权威 NS 从 DNSPod 切换到 Cloudflare。不要把“修改注册商 NS”误当成在 DNSPod 记录表里新增 NS 记录。

## 操作模式

- 用户要求直接代操作时，使用可用的浏览器控制能力，并优先接管用户已登录的腾讯云和 Cloudflare 标签页。
- 用户只要教程或检查清单时，仅提供指导，不修改线上状态。
- 账户中有多个域名时，必须先确认目标域名；不要根据相似名称猜测。
- 登录、验证码或账号安全验证需要用户接管时，停在对应页面并明确说明下一步。
- 如果只是迁移某个子域而不是根域，不要套用完整区域迁移；改用子域委派或 Cloudflare 对应的部分设置方案。

## 成功标准

同时满足以下条件才算迁移完成：

1. Cloudflare 已创建目标根域区域，并显示两条专属 NS。
2. Cloudflare 的 DNS 记录与迁移前的有效记录一致；区域原本为空时已明确确认。
3. 注册商控制台显示 Cloudflare 的两条 NS，旧 DNSPod NS 已移除。
4. 公共解析器返回 Cloudflare NS。
5. 至少一台 Cloudflare 权威服务器能返回目标域的 SOA 和正确 NS 集合。

Cloudflare 控制台的 `Active` 状态可能晚于公共 DNS 生效。若注册商、公共解析器和 Cloudflare 权威服务器均已验证正确，不要反复修改 NS。

## 工作流

### 1. 识别域名与现状

记录目标根域、当前注册商、当前 NS、DNSSEC 状态和全部 DNS 记录。

在 Windows 上先查询公共状态：

```powershell
$domain = "example.com"
Resolve-DnsName -Name $domain -Type NS -Server 1.1.1.1 -DnsOnly
Resolve-DnsName -Name $domain -Type DS -Server 1.1.1.1 -DnsOnly
Resolve-DnsName -Name $domain -Type A -Server 1.1.1.1 -DnsOnly
Resolve-DnsName -Name $domain -Type AAAA -Server 1.1.1.1 -DnsOnly
Resolve-DnsName -Name $domain -Type MX -Server 1.1.1.1 -DnsOnly
Resolve-DnsName -Name $domain -Type TXT -Server 1.1.1.1 -DnsOnly
Resolve-DnsName -Name "www.$domain" -Server 1.1.1.1 -DnsOnly
```

仍要以当前 DNS 服务商的完整记录列表为准，因为 Cloudflare 快速扫描和常见主机名查询都可能漏掉自定义子域。

区域显示 0 条记录时，至少交叉确认：

- DNSPod/腾讯云记录管理确实为 0 条；
- Cloudflare 扫描结果为 0 条；
- 公共 DNS 没有根域、`www`、MX、TXT 等现有业务记录。

只有三者一致时才按“空区域”继续，并提醒用户：NS 迁移成功后域名仍不会指向网站或邮箱，直到添加实际记录。

### 2. 在 Cloudflare 创建区域

在 Cloudflare 中连接根域：

1. 进入域名概览并选择连接/添加域名。
2. 输入根域，不要输入 `www` 等主机名。
3. 默认选择免费计划，除非用户明确要求付费计划。
4. 使用自动扫描后逐项与原 DNS 服务商比较。
5. 补齐遗漏的 A、AAAA、CNAME、MX、TXT、SRV、CAA、DKIM、DMARC 等记录。
6. 记录 Cloudflare 分配的两条 NS，必须原样使用，不能自行替换。

代理状态要保守处理：

- 网站的 A、AAAA、CNAME 可在确认源站和用途后启用橙云。
- MX、SPF、DKIM、DMARC、第三方验证和非 HTTP 服务保持 `DNS only`。
- 不要在迁移过程中顺手改变记录内容、TTL 或邮件配置。

### 3. 检查 DNSSEC

更换 NS 前检查注册商 DNSSEC 页面和公共 DS 查询。

- 存在 DS 记录或注册商显示 DNSSEC 已启用时，先在原注册商关闭 DNSSEC。
- 关闭后确认父区不再返回旧 DS，再更换 NS。
- Cloudflare 区域激活后才重新开启 Cloudflare DNSSEC，并按其提供的数据在注册商发布新 DS。

DNSSEC 未清理就更换 NS 可能导致全域 `SERVFAIL`。

### 4. 在腾讯云注册商侧更换 NS

使用“域名注册”控制台，不是“云解析 DNS/DNSPod 记录管理”页面：

1. 打开 `域名注册 > 我的域名`。
2. 等待列表完全加载。腾讯云单页应用加载期间可能短暂显示“全部域名 0”，不要据此判断账号错误。
3. 打开目标域名的 `管理/基本信息`。
4. 在 `DNS 解析` 区域选择 `修改 DNS 服务器`。
5. 选择 `使用非腾讯云 DNS`。
6. 将两个输入框分别替换为 Cloudflare 分配的两条 NS，通常不带末尾句点。
7. 提交前再次核对目标域名和两个完整 NS 值。
8. 提交并读取成功提示；随后确认页面上的 DNS 服务商变为“其他”，NS 显示为 Cloudflare。

若无法修改，检查 `禁止更新锁`、账号权限、实名认证状态和域名是否确实归当前注册账号所有。能管理 DNSPod 区域不代表一定有注册商侧的 NS 修改权限。

### 5. 通知 Cloudflare 并验证传播

回到 Cloudflare：

1. 选择 `我已更新名称服务器` 或同等按钮。
2. 触发一次立即检查。
3. 使用本 Skill 的脚本验证公共解析器和 Cloudflare 权威服务器：

```powershell
& ".\scripts\verify_ns.ps1" `
  -Domain "example.com" `
  -ExpectedNs @("alice.ns.cloudflare.com", "bob.ns.cloudflare.com")
```

也可手动检查：

```powershell
nslookup -type=ns example.com 1.1.1.1
nslookup -type=ns example.com 8.8.8.8
nslookup -type=soa example.com alice.ns.cloudflare.com
nslookup -type=ns example.com alice.ns.cloudflare.com
```

验证时接受 NS 顺序不同，但集合必须完全一致。

### 6. 完成与交接

报告以下结果：

- 域名；
- 旧 NS 与新 NS；
- 迁移前后的记录数量；
- DNSSEC/DS 状态；
- 腾讯云提交结果；
- 1.1.1.1、8.8.8.8 和 Cloudflare 权威服务器的验证结果；
- Cloudflare 控制台是 Active 还是仍在内部验证；
- 域名当前是否已有可用的网站或邮件记录。

不要泄露账户 ID、区域 ID、API 令牌、手机号、邮箱或其他账号信息。

## 故障判断

- **腾讯云显示新 NS，公共 DNS 仍是旧 NS**：注册局或递归缓存尚未传播，继续等待，不要重复提交。
- **公共 DNS 已返回 Cloudflare，控制台仍等待验证**：确认 Cloudflare 权威 NS 能返回 SOA；若能，等待 Cloudflare 状态刷新。
- **更换后出现 SERVFAIL**：优先检查父区残留旧 DS、Cloudflare 区域不存在或 NS 填错。
- **更换后出现 NXDOMAIN**：通常是 Cloudflare 缺少所需记录，不是 NS 传播失败。
- **网站正常但邮件失败**：检查 MX、SPF、DKIM、DMARC 是否完整，邮件相关记录是否错误开启代理。
- **腾讯云找不到域名**：等待列表加载完成，进入 `我的域名` 搜索，并确认当前登录的是注册账号而非只有 DNSPod 权限的身份。
- **Cloudflare 警告区域为 0 条记录**：只有在原 DNS 区域和公共查询也确认为空时才继续。

## 官方参考

界面或规则发生变化时，先核对官方文档，不要猜测新的按钮或要求：

- Cloudflare 完整区域设置：<https://developers.cloudflare.com/dns/zone-setups/full-setup/setup/>
- 腾讯云修改 DNS 服务器：<https://cloud.tencent.com/document/product/242/62106>
