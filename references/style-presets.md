# Design DNA：选择适合内容的视觉预设

预设是可调整的设计参数，不是已经安装的 PowerPoint 母版。模板、品牌和用户指定风格始终优先。只有没有既定设计或用户明确要求重设计时才选预设。

| 预设 | 适用场景 | 页面气质 | 配置 |
| --- | --- | --- | --- |
| Midnight | 产品发布、技术演示、路演 | 午夜深色、薄荷绿重点、留白 | [midnight.json](../presets/midnight.json) |
| Editorial | 策略、品牌、研究 | 暖纸色、朱红重点、文字层级 | [editorial.json](../presets/editorial.json) |
| Blueprint | 教学、工程、复盘 | 浅底、蓝色标注、规则对齐 | [blueprint.json](../presets/blueprint.json) |

根据任务选择一个预设，只读取对应 JSON，不将三套方案全部套入一份正式演示稿。需要展示多个方向时才生成比较样稿。

`canvas` 和 `safe_margin_px` 使用 CSS px（96 DPI），`title_pt` 与 `body_pt` 使用 pt。转换到所选工具的单位后再使用，不能混用。`font_candidates` 是候选字体，逐项验证实际可用性与中文字形，不能假设已安装。

沿用 `background`、`foreground`、`accent` 形成主层级，`muted` 用于次要说明。图表可增加必要的分类色，不能为服从预设而使数据难以辨认。允许适当调整字号和布局，重点是持续的层级与可读性。

[三种风格的可编辑样稿](../examples/style-showcase.pptx) 使用同一组虚构数据比较效果，仅作视觉示例。样稿的字体选择需在接收设备验证。
