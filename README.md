# pptskill

用于 Codex 的 PPT 制作 skill，帮助把主题、资料或已有演示稿整理为可编辑的 PowerPoint 文件。

## 能做什么

- 根据受众和目的规划幻灯片内容，控制页数与讲述顺序。
- 制作中文或中英混排演示稿，保留用户模板与品牌要求。
- 修改现有 PPT，使用可编辑文本、表格与数据图表。
- 执行内容核对与逐页视觉检查，明确尚未验证的部分。
- 使用随附 Python 脚本只读抽取 PPTX 的页面、文本、备注和对象数量。

这是供 AI agent 使用的工作流与辅助脚本，不是独立运行的一键 PPT 生成器。实际生成及渲染需要宿主环境提供对应工具；检查脚本只依赖 Python 3 标准库。

## 安装到 Codex

在目标项目根目录执行，目标目录应当尚不存在：

```bash
mkdir -p .agents/skills
git clone https://github.com/carefreelove/pptskill.git .agents/skills/pptskill
```

也可以将仓库下载后放到个人 skill 目录 `~/.agents/skills/pptskill`。已有同名目录时先检查内容，不直接覆盖。Codex 会发现新 skill；未显示时重启 Codex。安装位置与发现机制参见 [OpenAI 官方 skill 文档](https://learn.chatgpt.com/docs/build-skills)。

## 使用示例

```text
使用 $pptskill，根据附件的季度经营数据，制作面向管理层的 8 页中文汇报。
总页数包含封面。沿用附件模板，图表要可编辑，不补造缺失数字。
```

```text
使用 $pptskill，修改这份 PPT 的第 3–5 页，简化文字并改善中文换行。
保留原有数据、图表、页数和其他页面。
```

```text
使用 $pptskill，为面向新员工的 15 分钟产品培训提供逐页大纲，暂时不要生成文件。
```

## 检查 PPTX

```bash
python3 scripts/inspect_pptx.py /path/to/deck.pptx > inspection.json
python3 -m unittest discover -s tests -v
```

脚本按演示顺序输出 JSON，不修改输入文件，也不会联网。它不能检查文本溢出、视觉效果或所有对象的可编辑性，不能取代渲染与人工查看。

## 文件结构

```text
pptskill/
├── SKILL.md
├── agents/openai.yaml
├── references/design.md
├── references/quality-check.md
├── scripts/inspect_pptx.py
└── tests/test_inspect_pptx.py
```

用户提供的演示材料及生成的 PPT 不会随安装自动上传到任何服务。
