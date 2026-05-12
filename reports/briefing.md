# 晨间简报 2026-05-12（周二）

> 今天日程相对轻松，下午 15:30 起有三个连续的小型会议（SonicBerry 内部周会、CIE Office Hour、M365 Memory Scrum），上午和傍晚是整块可支配时间。重点是跟进昨天 Data Unlock sync 关于 Copilot Feedback Dataset 的访问申请进展。

## 今日日程

| 时间 | 会议 | 参会人 | 备注 |
|------|------|--------|------|
| 08:05-09:05 | Researcher Flight Review [APAC friendly] | Shilpa Patel、Katrina Gonzales、Carlos Colon、Steven Bailey、Sveinar Rasmussen +90人 | Teams；周度 Researcher agent flight review（APAC 时段），大群可选择性参加 |
| 15:30-16:15 | **SonicBerry Internal Sync - Weekly** | Tianqi Zhao、Mirror Xu、Yi Cheng、Jianfeng Liu、Shiwei Zhang +4人 | Conf Rm BJW 2/8478 + Teams；团队内部周会 [需准备] |
| 16:00-16:30 | Copilot Insight Engine Office Hour (Asia & EU) | Jinghua Wang +492人 | Teams；CIE Office Hour，仅有问题时参加 |
| 17:00-17:30 | **M365 Memory Scrum** | Xin Yu、Haizhen Huang、Mirror Xu、Qianhui Huang、Ychi Gu +14人 | Teams；Memory 项目 scrum |
| 23:05-00:00 | BizChat Weekly Flight Review | Gaurav Anand +305人 | Teams；可选大群，按需关注 |

> 16:30 的 WorkBerry FT collab w/ STCA 已取消；21:35 的 Copilot Briefs Architecture Sync 也已取消。

## 本周预览

**周三 (05-13)**
- 14:00-15:00 SkillUp AI: AI-Empowered Engineering Organization Transformation (中文)
- 14:00-15:00 [APRD Security Learning] Spartan – AI-native data sanitization
- 16:00-16:30 [EU & Asia] SEVAL Office Hour
- 16:30-17:00 **Data Unlock sync**（小群 10 人，重点跟进）

**周四 (05-14)**
- 17:00-17:30 M365 Memory Scrum
- 17:10-18:00 MSAI USR BizChat CORE Quality - Deepdives

**周五 (05-15)**
- 08:30-09:00 LU DRI live site review
- 13:00-14:00 SkillUp AI: No Code Agents (英文)
- 16:30-17:00 [EU&ASIA] BizChat Offline evaluation office hour

## 昨日回顾

昨天主要围绕 **Copilot Feedback Dataset 访问申请** 推进：Ishani 已正式发出申请邮件（CC 到你），团队讨论了 Cloverport 环境与 Feedback PDC 的前置条件；你也在 Heron 跑 pipeline 时遇到 `ErrorApprovalUnauthorized`，已向 Alex Stein 请求 User Copilot 项目访问权限。此外与 Yi Cheng 持续在 AzureML 上调试 verl GRPO browsecomp 训练 job（docker 镜像不可用，需换用其他 docker）。

## 谁找过我

- **Ishani Chakraborty**（邮件 + Teams）— 已正式发出 CopilotFeedbackDataset 申请，邮件 CC 到你；同时在 sync 中讨论 Cloverport 环境前置条件 [仅通知/可跟进]
- **Yi Cheng**（P2P Teams）— 协助调试 AzureML 训练 job，提供了 example job 和 docker 替换建议 [已处理]
- **Tinghai Pang**（P2P Teams）— 请求 `jieli4_microsoft/browsecomp_agent_training` 仓库权限，你已加好 [已处理]
- **Ychi Gu**（P2P Teams）— python-multipart 包有新的 Component Governance 项需要修 [需回复]
- **Alex Stein**（Teams）— 在 Data Unlock sync 中讨论 Cloverport 环境，并等待你 Heron 项目访问授权的回应 [需回复]
- **Kai Guo**（邮件）— Sev 2 #795664162 REST availability 事故分析，涉及 3S team，FYI [仅通知]
- **Xiaobin Lin**（邮件）— O365 Core wiki 链接因页面误删后重编号失效，Daniela 在修复 [仅通知]

## 待处理事项

- 【Ychi Gu】修复 python-multipart 的 Component Governance 合规项
- 【Alex Stein / Heron】跟进 User Copilot 项目 Heron 访问授权，解除 `ErrorApprovalUnauthorized`
- 【Yi Cheng】继续调试 verl GRPO browsecomp qwen3-0.6b 训练 job，换用可用 docker
- 【Ishani】关注 Copilot Feedback Dataset 申请回复，必要时补充 workspace / subscription IDs
- 【Data Unlock】为周三 16:30 的 Data Unlock sync 准备进展（Feedback Dataset 申请状态、Cloverport 环境调研）

## 今日建议

1. **上午整块时间**（09:30-15:30）优先做两件事：① 修 python-multipart 的 Component Governance（合规类一般不能拖）；② 继续推进 AzureML 训练 job，趁着 Yi Cheng 还在线可以快速反馈。
2. **15:30 SonicBerry 周会**前花 10 分钟整理一下本周进展：Feedback Dataset 申请、训练 job 状态、Heron 访问问题，方便同步给 Tianqi。
3. **17:00 Memory Scrum**：如果上午没时间，可以利用 14:30-15:30 这段空档预先看一下 scrum board，准备简短 update。
4. 傍晚有整块时间，可以为周三 Data Unlock sync 准备材料，避免临时赶工。

## 文件动态

- **Data Unlock sync 2026-05-06.loop**（Fluid）— Sarah Elsharkawy 修改；包含 reward model 决策项（layer norm/batch norm 测试、embedding-based classifier 采用等），与本周 Data Unlock 议程相关。
