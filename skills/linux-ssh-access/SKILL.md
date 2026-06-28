---
name: linux-ssh-access
description: 当用户表达"想连接服务器/虚拟机""帮我 SSH 上去""连一下 Linux"等意图时使用。会一步步引导小白用户提供连接信息，完成首次连接后自动为当前设备配置免密登录。兼容 macOS 与 Linux 运行环境。
version: 1.2.0
user-invocable: true
---

# Linux SSH 连接（引导式 + 自动免密）

目标：从本地主机连接目标 Linux，确认远程命令可执行；若用密码登录，则连接成功后自动为当前设备配置免密登录，以后无需再输密码。

把用户当作第一次操作的小白：每一步只问一件事，等用户回答后再问下一步，不要一次性把所有问题抛出来。

---

## 阶段一：引导用户收集连接信息

### 步骤 0 — 一次性向用户收集所有连接信息

当识别到用户有 SSH 连接意图时，**一次性**把需要的信息都列出来，让用户一次回复齐全，不要逐项分多轮追问，避免来回打扰用户：

> 好的，我来帮你连接 Linux 服务器，并在连接成功后自动配置免密登录（以后就不用再输密码了）。
>
> 请一次性提供以下信息：
>
> 1. **服务器 IP 或主机名**：例如 `192.168.1.100`
> 2. **登录用户名**：例如 `root`（生产环境建议用普通用户）
> 3. **SSH 端口**：不确定就填 `22`
> 4. **认证方式**（二选一）：
>    - **密码**：直接把密码发我（仅用于本次连接，不存盘、不在后续回复中重复）
>    - **密钥**：已配过免密，提供密钥路径（默认 `~/.ssh/id_rsa`）
>
> 你可以直接按这个格式回复，例如：
> ```
> IP: 192.168.1.100
> 用户: root
> 端口: 22
> 密码: yourpassword
> ```
>
> 或者直接给我完整命令也行，例如 `ssh root@192.168.1.100`。

收到回复后，从中解析出：用户名、主机、端口（缺省默认 `22`）、认证方式与凭证。

**如果用户回复里有缺项**，只补问缺失的那一项，不要把所有问题再重复一遍。例如只缺端口就问"端口是多少？不确定我用 22"，缺密码就问"请把密码发我"。

### 步骤 1 — 汇总确认

把收集到的信息整理给用户确认，**密码一律显示为 `***`**，不要原样回显：

> 已收到连接信息：
> - 主机：`192.168.1.100`
> - 用户：`root`
> - 端口：`22`
> - 认证：密码（已收到 `***`）
>
> 确认无误吗？回复"确认"我就开始连接；如需修改请告诉我改哪一项。

用户确认后才进入阶段二执行连接。

---

## 阶段二：技术执行流程

### 1. 检查端口

```bash
nc -z -w5 <host> <port> && echo "port open" || echo "port closed"
```

端口不通时停止，向用户报告"端口不通，无法连接"，不继续认证。

### 2. 选择认证方式

#### SSH Key

当用户已配置密钥或免密登录时使用：

```bash
ssh -o BatchMode=yes -o ConnectTimeout=10 \
  -p <port> <user>@<host> "hostname && whoami && uname -s"
```

密钥认证失败时报告错误。若用户另行提供密码，再切换到密码认证。

#### 密码（sshpass）

优先使用 `sshpass`。macOS 需先安装：

```bash
brew install hudochenkov/sshpass/sshpass
```

通过临时环境变量传递密码，避免出现在命令行参数和进程列表中：

```bash
read -rs SSH_PASSWORD
export SSH_PASSWORD

sshpass -P "assword" -p "$SSH_PASSWORD" ssh \
  -o BatchMode=no \
  -o PubkeyAuthentication=no \
  -o PreferredAuthentications=password,keyboard-interactive \
  -o PasswordAuthentication=yes \
  -o NumberOfPasswordPrompts=1 \
  -o ConnectTimeout=10 \
  -o StrictHostKeyChecking=accept-new \
  -p <port> <user>@<host> \
  "hostname && whoami && uname -s"

unset SSH_PASSWORD
```

#### 密码（expect 回退）

当 `sshpass` 不可用时，使用 expect 脚本。从标准输入读取密码，不写入磁盘：

```bash
read -rs SSH_PASSWORD
export SSH_PASSWORD

expect <<'EOF'
set timeout 15
set password $env(SSH_PASSWORD)
spawn ssh \
  -o PubkeyAuthentication=no \
  -o PreferredAuthentications=password,keyboard-interactive \
  -o PasswordAuthentication=yes \
  -o NumberOfPasswordPrompts=1 \
  -o ConnectTimeout=10 \
  -o StrictHostKeyChecking=accept-new \
  -p <port> <user>@<host> \
  "hostname && whoami && uname -s"
expect {
  -re "(P|p)assword:" { send "$password\r"; exp_continue }
  -re "(yes/no)" { send "yes\r"; exp_continue }
  eof
}
EOF

unset SSH_PASSWORD
```

`accept-new` 只适用于用户确认的个人或实验虚拟机。主机指纹冲突时停止并报告用户。

### 3. 备用方式：Paramiko

`sshpass` 与 `expect` 均不可用时，可改用 Paramiko。

先检查：

```bash
python3 -c "import paramiko; print(paramiko.__version__)"
```

缺少 Paramiko 时先询问用户是否同意安装，不自动安装。

使用 Paramiko 时：

- 从临时环境变量 `SSH_PASSWORD` 读取密码
- 返回退出码、标准输出和错误输出
- 执行后清理密码环境变量

辅助脚本：

```bash
python3 {baseDir}/scripts/ssh_connect.py --host <host> --port <port> --user <user>
```

### 4. 成功标准

必须同时满足：

- SSH 命令退出码为 `0`
- `hostname` 和 `whoami` 有输出
- `uname -s` 返回 `Linux`

连接成功后向用户反馈：

> ✅ 连接成功！
> - 主机名：`xxx`
> - 当前用户：`xxx`
> - 系统：Linux
>
> 后续你要在服务器上执行的命令，我都会通过这条 SSH 通道运行。

后续 Linux 命令必须在该远程主机执行。

---

## 阶段三：自动配置免密登录（仅密码认证时）

当用户本次用**密码**登录成功后，主动询问是否配置免密，让小白明白接下来要做什么：

> ✅ 连接成功！
> - 主机名：`xxx`
> - 当前用户：`xxx`
> - 系统：Linux
>
> 接下来我帮你配置免密登录——配好之后，以后连这台服务器就不用再输密码了，我会自动用密钥登录。
>
> 现在配置吗？（回复"是"或"否"，建议选"是"）

用户同意后才执行下面的步骤。**用户已用密钥登录的，跳过本阶段。**

### 1. 检查本地是否已有 SSH 密钥

优先查找 `ed25519`，其次 `rsa`：

```bash
ls -1 ~/.ssh/id_ed25519.pub ~/.ssh/id_rsa.pub 2>/dev/null
```

- 已有公钥：直接用现有公钥，跳到「3. 推送公钥」。
- 没有公钥：进入「2. 生成密钥」。

### 2. 生成 SSH 密钥（本地没有时）

```bash
ssh-keygen -t ed25519 -f ~/.ssh/id_ed25519 -N "" -C "$(whoami)@$(hostname)-autogen"
```

- `-N ""` 表示空密码（免密密钥），对小白友好。
- 生成后告知用户：本地密钥已生成，存放在 `~/.ssh/id_ed25519`。

### 3. 推送公钥到远程主机

把当前设备的公钥追加到远程 `~/.ssh/authorized_keys`，让本设备以后可免密登录。

#### 方式一：ssh-copy-id（优先）

```bash
# 密码仍通过临时环境变量传递，不进命令行参数
sshpass -P "assword" -p "$SSH_PASSWORD" \
  ssh-copy-id -i ~/.ssh/id_ed25519.pub \
  -o StrictHostKeyChecking=accept-new \
  -p <port> <user>@<host>
```

#### 方式二：手动追加（ssh-copy-id 不可用时）

```bash
PUBKEY=$(cat ~/.ssh/id_ed25519.pub)
sshpass -P "assword" -p "$SSH_PASSWORD" ssh \
  -o StrictHostKeyChecking=accept-new \
  -p <port> <user>@<host> \
  "mkdir -p ~/.ssh && chmod 700 ~/.ssh && \
   touch ~/.ssh/authorized_keys && chmod 600 ~/.ssh/authorized_keys && \
   grep -qF '$PUBKEY' ~/.ssh/authorized_keys || echo '$PUBKEY' >> ~/.ssh/authorized_keys"
```

`grep -qF` 防止重复追加同一公钥。

#### 方式三：expect 回退（sshpass 不可用时）

```bash
PUBKEY=$(cat ~/.ssh/id_ed25519.pub)
expect <<EOF
set timeout 15
set password \$env(SSH_PASSWORD)
spawn ssh -o StrictHostKeyChecking=accept-new -p <port> <user>@<host> \
  "mkdir -p ~/.ssh && chmod 700 ~/.ssh && touch ~/.ssh/authorized_keys && chmod 600 ~/.ssh/authorized_keys && grep -qF '$PUBKEY' ~/.ssh/authorized_keys || echo '$PUBKEY' >> ~/.ssh/authorized_keys"
expect {
  -re "(P|p)assword:" { send "\$password\r"; exp_continue }
  -re "(yes/no)" { send "yes\r"; exp_continue }
  eof
}
EOF
```

推送后 `unset SSH_PASSWORD`，密码不再保留。

### 4. 验证免密登录是否生效

用 `BatchMode=yes` 强制只走密钥、不提示密码，验证免密是否真的成功：

```bash
ssh -o BatchMode=yes -o PubkeyAuthentication=yes \
  -o PreferredAuthentications=publickey \
  -o ConnectTimeout=10 \
  -p <port> <user>@<host> "echo passwordless-ok"
```

- 输出 `passwordless-ok`：免密配置成功。
- 无输出或报错：配置失败，向用户报告原因（可能是远程 `sshd_config` 禁用了 `PubkeyAuthentication`，或目录权限不对），不要谎报成功。

### 5. 反馈用户 + 提供自助登录命令

配置成功后，把一条**用户可直接复制粘贴就能登录**的命令交给用户，让他自己也能随时连上去验证免密是否真的生效。

标准端口（`22`）给精简命令，非标准端口给带 `-p` 的完整命令：

#### 标准端口 22 时

> ✅ 免密登录配置成功！
> - 本地密钥：`~/.ssh/id_ed25519`
> - 已写入远程：`~/.ssh/authorized_keys`
>
> 以后再连这台服务器，我会自动用密钥登录，你不用再提供密码了。
>
> 你自己也可以随时登录——把下面这条命令复制到终端，回车就能直接进去，不用输密码：
>
> ```
> ssh root@192.168.1.100
> ```
>
> 如果能直接进入服务器（不再提示输入密码），说明免密配置完全成功。
>
> 后续你要在服务器上执行的命令，我都会通过这条免密通道运行。

#### 非标准端口时

> ✅ 免密登录配置成功！
> - 本地密钥：`~/.ssh/id_ed25519`
> - 已写入远程：`~/.ssh/authorized_keys`
>
> 以后再连这台服务器，我会自动用密钥登录，你不用再提供密码了。
>
> 你自己也可以随时登录——把下面这条命令复制到终端，回车就能直接进去，不用输密码：
>
> ```
> ssh -p 2222 admin@10.0.0.5
> ```
>
> 如果能直接进入服务器（不再提示输入密码），说明免密配置完全成功。
>
> 后续你要在服务器上执行的命令，我都会通过这条免密通道运行。

**生成命令时用实际值替换 `<user>`、`<host>`、`<port>`，不要留占位符**。端口为 `22` 时省略 `-p 22`，让命令更简洁。

配置失败时如实告知，并给出排查建议（检查远程 `sshd_config` 的 `PubkeyAuthentication yes`、`~/.ssh` 权限 `700`、`authorized_keys` 权限 `600`），同时仍把基础连接命令给用户，让他可以用密码方式手动登录排查。

### 6. Paramiko 回退说明

当 `sshpass` 与 `expect` 均不可用、只能用 Paramiko 首次连接时，免密配置暂不支持自动完成（Paramiko 无 `ssh-copy-id` 等价能力）。此时应：

1. 用 Paramiko 完成首次连接验证。
2. 明确告知用户："当前环境缺少 sshpass/expect，无法自动配置免密。建议安装后重新执行，或手动运行 `ssh-copy-id -p <port> <user>@<host>`。"
3. 不谎称已配置免密。

---

## 安全规则

- 非实验环境优先使用 SSH Key。
- **不把密码写入仓库、长期脚本、命令参数或最终回复**。汇总确认和成功反馈时密码均显示为 `***`。
- 密码通过临时环境变量传递，使用后立即 `unset`。
- 免密配置成功后，密码不再保留在任何地方，后续连接一律走密钥。
- 认证失败最多重试两次，每次重试前告知用户。
- 不自动覆盖已有主机指纹。
- 不自动覆盖远程已有的 `authorized_keys`，推送公钥前用 `grep -qF` 去重。
- 不默认使用 `root`；用户主动指定 `root` 时提醒一次"建议使用普通用户"。
- 密钥生成用空密码（`-N ""`）时仅限个人/实验设备，生产环境应提示用户设置密钥密码。
