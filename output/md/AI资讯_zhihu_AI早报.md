# OpenAI发文宣布2025年收入超200亿美元；谷歌称暂无在 Gemini 应用投放广告的计划【AI 早报 2026-01-19】
橘鸦Juya - https://api.zhihu.com/articles/1996500587794174358
![](https://pic4.zhimg.com/v2-39dad13718a3c93b21cddecb2214f6c5_1440w.jpg)

*不好意思忘发了*

## AI 早报 2026-01-19

## 概览

- OpenAI发文宣布2025年收入超200亿美元 `#1`
- Google副总裁确认Gemini暂无广告计划 `#2`
- Warp发布CLI编程Agent深度支持功能 `#3`
- GitLab发布GitLab Duo Agent Platform `#4`
- Claude Code 新增执行 Plan 前自动清除Context功能 `#5`
- Anthropic正为Claude开发定制化命令功能 `#6`

---

## OpenAI发文，宣布2025年收入超200亿美元 `#1`

>  OpenAI 2025年收入突破200亿美元，计算能力大幅提升，未来将聚焦 Agent 自动化与医疗科学等领域的商业化探索。

**OpenAI** 官方发文，宣布其 **2025年** 年度经常性收入（`ARR`）已突破 **200亿美元**，相较于 **2023年** 的 **20亿美元** 实现了 **10倍** 增长。官方数据显示，这一增长与计算资源的扩张高度同步，其计算能力从 **2023年** 的 **0.2 GW** 提升至 **2025年** 的约 **1.9 GW**。

目前 **OpenAI** 已构建起涵盖个人与职场订阅、`API`、广告及商业服务的多元化商业模式，其周活跃用户（`WAU`）与日活跃用户（`DAU`）均创历史新高。面向 **2026年**，**OpenAI** 将重点推动“实际采用”（Practical Adoption），发展能够跨工具执行任务的 `Agent` 和工作流自动化系统，并计划在医疗、科学及企业领域探索按成果定价等新型经济模式。

在财务与运营策略上，**OpenAI** 坚持保持轻资产负债表，通过合作伙伴关系而非自持资源，并分阶段根据需求信号投入资金，以保持应对市场变化的灵活性。

![](https://picx.zhimg.com/v2-52b08a919c1ae73cfd0043898fb6a6f7_1440w.jpg)

```text
https://openai.com/index/a-business-that-scales-with-the-value-of-intelligence/
```

---

## Google副总裁确认Gemini暂无广告计划 `#2`

>  Google 明确表示目前不会在 Gemini 应用中投放广告，商业化重心仍集中在 AI 搜索功能的广告转化上。

**Google** 全球广告副总裁 **Dan Taylor** 近日接受媒体采访时表示，目前没有在 `Gemini` 应用中投放广告的计划，公司的商业化重心将优先放在 `AI Overviews` 和 `AI Mode` 等 AI 搜索功能上。

官方数据显示，`AI Overviews` 广告的参与率已与传统搜索广告基本持平，月活跃用户已突破 **20 亿**。

![](https://pic1.zhimg.com/v2-a46eb46cc90f773fe0db9e1456645cea_1440w.jpg)

```text
https://www.businessinsider.com/google-vp-says-ads-arent-coming-to-gemini-yet-why-2026-1
```

---

## Warp发布CLI编程Agent深度支持功能 `#3`

>  Warp 终端通过集成语音转录和图像支持，深度优化了 Claude Code 等多个编程 Agent 的使用体验。

**Warp** 官方近日宣布为 `CLI` coding `Agent` 提供原生深度支持。该功能通过集成 `WisprFlow` 提供的内置语音转录功能、支持提示词附加图像，以及在终端内直接浏览文件和审阅代码等特性，全面提升了包括 `Claude Code`、`Codex`、`Amp`、`Gemini` 和 `Droid` 在内的多个 `Agent` 工具的使用体验。

![](https://pic4.zhimg.com/v2-bedc0bb25f501b8bd4b2b9f0f564e273_1440w.gif)

```text
https://x.com/warpdotdev/status/2012280061143945437
```

---

## GitLab发布GitLab Duo Agent Platform `#4`

>  GitLab Duo Agent Platform 正式商用，通过多步推理和自定义 Agent 能力，将 AI 自动化覆盖至软件开发全生命周期。

**GitLab** 近期宣布 `GitLab Duo Agent Platform` 正式进入全量商用（`GA`）阶段，旨在通过 `Agentic AI` 自动化能力解决软件交付中的“AI 悖论”，将 AI 的效率提升从单纯的代码编写扩展至整个软件开发生命周期。

该平台引入了具备多步推理能力的 `Duo Agentic Chat`，并提供由 **GitLab** 预置的 `Foundational Agent`、允许企业通过 `AI Catalog` 构建的 `Custom Agent` 以及集成外部工具的 `External Agent`，如 `Claude Code` 和 `Codex CLI`。

![](https://pic1.zhimg.com/v2-4152e7cb6525d7a873e41fdcec1d809c_1440w.jpg)

```text
https://about.gitlab.com/blog/gitlab-duo-agent-platform-is-generally-available/
https://docs.gitlab.com/user/duo_agent_platform/
```

---

## Claude Code 新增执行 Plan 前自动清除Context功能 `#5`

>  Claude Code 引入自动清除上下文功能，旨在通过刷新 Context Window 提升模型对复杂任务计划的执行专注度。

`Claude Code` 近期引入了一项功能更新，当用户在工具中接受一个 `Plan` 时，系统将自动清除当前的 `Context`，从而为执行该 `Plan` 提供一个全新的 `Context Window`。

根据官方人员 **Boris Cherny** 的说明，此项改动旨在帮助 `Claude` 在处理任务时更长时间地保持专注，并显著提升其对 `Plan` 的执行依从性。与此同时，对于有特殊需求、不希望在接受 `Plan` 时清除 `Context` 的用户，`Claude Code` 依然保留了相关选项以供选择。

![](https://pica.zhimg.com/v2-1e5b734ecce56eaebd13fe930ebe5702_1440w.jpg)

```text
https://x.com/bcherny/status/2012663636465254662
```

---

## Anthropic正为Claude开发定制化命令功能 `#6`

>  Anthropic 正在开发全新的 Customize 模块，允许用户为 Claude Code 自定义命令并集中管理技能与插件权限。

据 **testingcatalog** 报道，**Anthropic** 正在为 `Claude` 开发一项名为 `Customize` 的新功能模块，该模块位于左侧边栏的 `Projects` 和 `Artifacts` 下方，旨在集中管理 `Skills`、`Connectors` 以及针对 `Claude Code` 的新功能 `Commands`。

通过该功能，用户可以创建并浏览技能，直接在应用内预览 `HTML` 文件或查看纯文本文件，同时集中管理 `Connector` 的插件连接与权限设置。此外，用户将能够为 `Claude Code` 定义包含名称、描述和指令的自定义 `Commands`。

虽然技术细节显示该功能在内部触发 `commands/create-simple-command`，但目前仍处于早期开发阶段，尚未正式向公众发布，其目标是进一步提升 `Claude` 桌面端及技术工作流的模块化与可配置性。

![](https://pica.zhimg.com/v2-9e54cda41b30a414ad5eb4b056716108_1440w.jpg)

```text
https://www.testingcatalog.com/anthropic-works-on-customizable-commands-for-claude-code/
```

---

**提示**：内容由AI辅助创作，可能存在**幻觉**和**错误**。

作者`橘鸦Juya`，视频版在同名**哔哩哔哩**。欢迎**点赞、关注、分享**。

![](https://picx.zhimg.com/v2-f4acd95565375f10f7f5ce5a48ceca05_1440w.jpg)

---