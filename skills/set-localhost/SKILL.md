---
name: set-localhost
description: Interactive one-time binding of "本机" (the user's own device on the tailnet) for the mybox + tmux-ssh-remote toolchain. Trigger when the user says "设置本机 / 绑定本机 / 配置我的电脑 / 换绑我的机器 / set localhost / 初始化 mybox / 我的本机还没配置" or when mybox reports 未找到 .mybox.conf and the user wants to set it up. Flow — list tailscale peers as a popup choice, write the person's .mybox.conf via mybox set, hand the user a copy-paste ssh-copy-id command (run as winbeau) to install the public key + accept the host key once, then after the user replies ok, auto-verify through the tmux-ssh-remote skill.
---

# set-localhost

一次性把"本机"(用户自己的 tailscale 设备)绑定到 mybox,并完成公钥安装与
tmux-ssh-remote 验证。背景:claude 出站 ssh 恒以 winbeau 的 uid/密钥运行,
mybox 用 pwd 定位工作区(见 `/home/winbeau/bin/mybox help`)。

## 流程

### 1. 前置解析

在**用户工作区目录**(会话项目目录,勿在 /tmp)执行:

```bash
/home/winbeau/bin/mybox whoami     # 确认工作区定位正确;报错则让用户先 cd 到工作区
tailscale status                   # 机器列表
tailscale ip -4                    # 本服务器自身 IP —— 从候选中剔除
```

若 `.mybox.conf` 已存在,先 `mybox show` 给用户看当前绑定,确认是要**换绑**再继续。

### 2. 先给全表,再弹窗选择

AskUserQuestion 最多 4 个选项,而 tailnet 常有十几台机器装不下。所以**先在正文
输出一张覆盖全部 peer 的 markdown 表格**(在线在前),让用户能看全、能复制 IP;
**再**发弹窗。

**2a. 全机器表格(正文,不是弹窗):**

- 解析 `tailscale status`,剔除本服务器自身 IP(`tailscale ip -4` 得到)。
- 按 online 在前、offline 在后排序;offline 的标注"离线(最后 N 前在线)"。
- 列:`# | 主机名 | tailscale IP | 所属账号 | 状态`。编号从 1 开始。
- 表下一句提示:"下面弹窗只列前几台;你的机器不在选项里就复制上表的 IP,选 Other 粘进去"。

**2b. 第一轮弹窗(机器 + 端口,一次调用 2 问):**

- **Q1 选机器**:选项放**在线的前 3 台**(label=主机名短名,description=`IP · 所属账号`),
  第 4 个位置留给列表外的机器(问题文本写明"不在这 3 个里就选 Other,从上表复制 IP 填入")。
  绝不替用户猜/默认选一台。
- **Q2 SSH 端口**:22 (Recommended) / 2222 / Other。WSL 常见 2222。

**2c. 第二轮弹窗(远端用户名,单独一问,等第一轮选完再发):**

- **第一个选项必须是 `/home/?` 解析出的名字**(即 `mybox whoami` 的工作区名,
  如 wenbiao_zhao);后面给 winbeau / 由所选机器主机名或所属账号推断的名字
  (如 desktop-jackrainman → rainman,有把握才给)。
- 问题文本注明:"这是你**那台设备上**的登录名(Windows/Mac/Linux 用户名),
  都不是就选 Other 自己填"。用户自输入走 Other,原样采用。

### 3. 写配置

在工作区目录执行,并把结果原样给用户看:

```bash
/home/winbeau/bin/mybox set <user>@<ip>[:port]
```

跳板/嵌套 ssh 等复杂场景不走本流程,改用
`mybox set --ssh-cmd "..."` 并提示用户手动装公钥。

### 4. 让用户手动连一次(装公钥 + 首次 host key yes)

生成命令给用户**自己复制执行**(需要交互输密码,claude 不能代跑)。
必须以 winbeau 身份连(claude 出站 ssh 恒为 winbeau 的 uid/密钥):

- 工作区在 `/home/winbeau/<姓名>/` 下(用户终端本来就是 winbeau):

  ```bash
  ssh-copy-id -i /home/winbeau/.ssh/id_ed25519.pub -p <port> <user>@<ip>
  ```

- 工作区在 `/home/<用户>/` 下(真实 Linux 用户终端,需切到 winbeau):

  ```bash
  sudo -u winbeau -H ssh-copy-id -i /home/winbeau/.ssh/id_ed25519.pub -p <port> <user>@<ip>
  ```

(`-p <port>` 仅在非 22 时加。)告诉用户:开自己的终端跑上面的命令
(需要交互输密码),跑完**回复 ok**。然后**结束本轮等待用户**——
不要自己去跑 ssh-copy-id,也不要在用户确认前就开始验证。

### 5. 用户回复 ok 后:自动验证

```bash
/home/winbeau/bin/mybox doctor     # TCP + 免密应当全"通";失败把输出给用户排查
```

doctor 通过后走 tmux-ssh-remote skill 正式验证:

```bash
SESSION=$(basename "$(git rev-parse --show-toplevel 2>/dev/null || pwd)")
SSH_CMD=$(/home/winbeau/bin/mybox ssh-cmd)
~/.claude/skills/tmux-ssh-remote/tmux-ensure.sh "$SESSION" "$SSH_CMD"
~/.claude/skills/tmux-ssh-remote/tmux-inject.sh -t 30 --auto-recover "$SESSION" 'hostname && whoami'
```

`hostname`/`whoami` 与所选机器/用户名对上 → 宣布绑定完成,
以后说"连到本机"即可直连。对不上或失败 → 把输出给用户,一起排查
(常见:选错机器、远端用户名不对、对方 sshd 未开)。

## Pitfalls

- **mybox 定位靠 pwd**:所有 mybox 调用都要在用户工作区目录里执行。
- **不要替用户选机器或猜 IP**;用户不选就停在弹窗。
- **不要自己跑 ssh-copy-id**(交互密码),那一步永远交给用户。
- doctor "TCP 通但认证失败"且用户说已装公钥 → 检查装到的是不是
  winbeau 的公钥(`/home/winbeau/.ssh/id_ed25519.pub`),而不是用户自己的。
- 对方是 Windows 原生 sshd 时 authorized_keys 规则不同
  (管理员账户用 `administrators_authorized_keys`),ssh-copy-id 可能装了也不生效,
  提示用户装到 WSL 的 sshd 或按 Windows 文档处理。
