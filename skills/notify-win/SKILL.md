---
name: notify-win
description: 向 Windows 桌面弹一条通知（静音 toast + 响亮报警铃）。当用户说"通知到win/通知到windows/通知我/弹窗通知我/做完通知我/跑完通知我/弹个窗提醒我"，或英文 "notify me on windows / ping my windows / send a windows toast / windows notification" 时使用；常见于长任务（训练、构建、下载）跑完后提醒用户回到 Windows 桌面。
when_to_use: 用户想在 Windows 桌面收到弹窗+响铃提醒。触发短语（中）：通知到win、通知到windows、通知我（到windows）、弹窗通知我、做完通知我、跑完通知我、任务完成通知、弹个窗。触发短语（英）：notify me on windows、ping my windows、windows toast、pop a windows alert、send me a windows notification。不要用于：邮件/Slack/手机推送等非 Windows 桌面通知。
allowed-tools: Bash
---

# notify-win — 向 Windows 桌面弹通知

从这台 Ubuntu 经 SSH 在 Windows 桌面（`<user>@<win-host>`，Tailscale 主机）弹一条**静音 toast + 响亮报警铃**。CLI 已在 PATH：`notify-win`。

## 用法

```
notify-win -m <正文> [-t <标题>] [-q]
```

- `-m <正文>` 通知正文。**必填**（或管道：`echo 正文 | notify-win`；同时给则以 `-m` 为准）。
- `-t <标题>` 标题。可选，默认 `Ubuntu 通知`。
- `-q` 静音（只弹窗、不响铃）。

> 声音是**固定的响亮报警音**，以系统绝对 40% 音量播放、放完自动还原（与当前音量无关，不受免打扰影响）。`-s` 仍可传但**不改变声音**。中文/emoji/引号/空格/换行全部安全，无需转义。

## 消息怎么写（机械规则）

1. **标题 `-t`** = 类别 emoji + 短标签：`✅ 构建完成` / `❌ 训练失败` / `⚠️ 磁盘将满` / `❓ 待确认` / `ℹ️ 进度`。
2. **正文 `-m`** = 实际内容：结果、关键数字、错误摘要（一两句）。
3. 用 emoji 区分场景（声音统一，靠 emoji+标题辨识）。
4. 长内容只放摘要 + 关键数字，不贴大段日志。
5. 绝不把密钥/token/密码放进通知。
6. 用户要安静 → 加 `-q`。

## 示例

```bash
notify-win -t '✅ 构建完成' -m '训练 120 epoch 跑完, acc=0.93'
long_task && notify-win -t '✅ 完成' -m '任务完成' || notify-win -t '❌ 失败' -m '任务挂了, 见 log'
echo '管道里的消息' | notify-win -t 'ℹ️ 提醒'
notify-win -q -t 'ℹ️ 就绪' -m '后台已就绪'   # 静音
```

典型流程：用户让你跑长任务并"做完通知我" → 任务结束后按成功/失败选 emoji+标题+正文，调一次 `notify-win`。

## 退出码与失败处理

退出码 = SSH 的退出码；**非零即失败**（不要假定具体数值）：

- `0` 成功（消息已投递并触发桌面弹窗+响铃）。
- `1` 用法错误（通常漏了 `-m`/正文为空）。
- `255` SSH/传输失败：Windows 关机、不在 Tailscale 网内、SSH 未起、连接超时。
- 其它非零：远端执行失败。

排错：
1. `command not found` → CLI 没装/不在 PATH（查 `~/.local/bin/notify-win`）。
2. 退出 255 → 主机不可达：`ssh -p 22 <user>@<win-host> echo ok` 验证；确认 Windows 开机且在 Tailscale。
3. 退出 0 但桌面没弹窗 → Windows「PowerShell 通知权限」被关或计划任务未就绪（见 memory `project_notify_win.md`）；声音不受此影响。

失败时不要静默——把退出码和最可能原因报告给用户。

## 配置

主机/用户/端口/密钥在 `~/.config/notify-win/config`。Windows 端声音/音量在 `~/.notify-win\show.ps1`（`$WAV` 改铃声、`$VOL` 改绝对音量百分比）。

> **首次部署 / 新机重建**：本 skill 目录已自带 Linux CLI + Windows 端脚本与模板——`notify-win`、`config.example`、`show.ps1`、`launcher.vbs`、`notify-setup-v2.ps1`、`notify-finish.ps1`。架构、踩坑与逐步部署见同目录 [`README.md`](./README.md)。上游 canonical 仓库：<https://github.com/winbeau/notify-win>。
