# Deck Doctor

只读、离线、Python 3 标准库实现。接收未加密 `.pptx`，输出带页码、证据和修改建议的 Markdown 或 JSON。

```bash
python3 scripts/deck_doctor.py deck.pptx
python3 scripts/deck_doctor.py deck.pptx --expected-slides 8 --max-chars 280
python3 scripts/deck_doctor.py deck.pptx --format json > report.json
python3 scripts/deck_doctor.py deck.pptx --strict
```

从其他目录调用时使用脚本的实际路径。`--expected-slides` 必须来自交付约束，计数包含隐藏页。`--max-chars` 默认为每页 320 个非空白字符，数字、标点和英文字符同样计数，因此它只是可调整的密度提示，不是阅读时长或溢出的测量。

| 规则 | 级别 | 含义 |
| --- | --- | --- |
| `empty-deck` | error | 演示文稿没有页面 |
| `slide-count` | error | 实际总页数与传入约束不符 |
| `placeholder` | warning | 检测到 TODO、TBD、待补充等候选占位文本 |
| `text-density` | warning | 普通文本的非空白字符数超过配置阈值 |
| `image-only-candidate` | warning | 存在图片，未抽取到普通文本或原生表格、图表 |
| `hidden-slide` | info | 存在隐藏页 |
| `repeated-opening` | info | 多个可见页的首段相同，可能是正常的品牌重复 |

默认遇到 error 返回退出码 `1`，只有 warning 或 info 时返回 `0`。`--strict` 将 warning 也计为退出码 `1`。输入无法读取或参数无效返回 `2`。报告写入 stdout，读取错误写入 stderr。

所有提示保留原始文件不变。隐藏页仍执行内容规则。母版内容、图片中文字和复杂对象可能无法抽取；XML 中的首段也不一定是视觉标题。没有提醒不表示文件可以正常渲染、数据正确或全部内容可编辑。

不联网，不调用模型，不产生“美观度评分”。渲染和逐页审阅继续按 [交付前检查](quality-check.md) 执行。
