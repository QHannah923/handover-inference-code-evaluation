# Interface Interference：语音暗黑模式识别与规则评估

项目读取完整的用户与Alexa技能对话，联合识别Interface Interference下的父类型与子类型，再用独立证据规则补充或纠正明确的边界情形。当前实现范围是Interface Interference；完整taxonomy的其他类别不代表已完成验证。

当前模型配置是`gpt-6.1-sol`，推理强度`high`。产品植入和原生广告已合并。用户人工参照是本项目的操作性参照，并非第三方正式金标准。

## 先看这些文件

- [现行独立规则](dark-pattern/verified_failure_rules.py)：成立条件、排除条件、原文证据和规则采用逻辑。
- [现行提示词](dark-pattern/interface_interference_prompt_v2.py)与[广告判据](dark-pattern/ad_subtype_policy.py)。
- [提示词与规则阅读指南](当前prompt与rules_详细解读.md)。
- [最新七条复读及升级报告](outputs/interface_boundary_rules_20261120/七条复读与规则升级结果.md)。
- [最新87条预测](outputs/interface_boundary_rules_20261120/predictions.json)及[逐项人工评分](outputs/interface_boundary_rules_20261120/逐项人工核对与结果.json)。
- [固定人工参照](outputs/interface_semantic_freemium_20261120/用户新版参照_87条_20261120.json)。
- [87条原始对话](dark-pattern/interface_interference_examples/INTERFACE_INTERFERENCE_all(87))：保留准确原文件名。

## 结果如何解释

全部结果基于同一批87条开发样本，包含31条Sleep Better相关样本。一级弃判按“没有暗黑模式”计分；只有子类型弃判仍算二级路径不完整。多标签样本只统计主路径是否命中任一人工允许路径，不代表所有标签均完整检出。准确率为逐项人工核对后录入，仓库脚本不自动匹配参照计分。

- 历史已保存输出＋旧规则：一级73/87＝83.91%，二级68/87＝78.16%。
- 同一历史输出＋增强规则：一级82/87＝94.25%，二级77/87＝88.51%。这是规则重放对照。
- 放宽语义提示词后重新运行：一级76/87＝87.36%，二级71/87＝81.61%。该版本已回退，保留负面结果和快照。
- 保留配置重新运行：一级80/87＝91.95%，二级75/87＝86.21%。
- 在上述同一次运行的原始答案上应用最新边界规则：一级84/87＝96.55%，二级79/87＝90.80%。修正5、7、14、32号，其余83条主路径不变；没有再次调用模型。

96.55%不是独立测试集准确率，也不是全taxonomy的准确率。剩余一级分歧为50、82、83号，另有40、53、64、81、87号子类型分歧。下一步应统一这些边界，再用未参与开发的新对话验证。

## 目录

```text
dark-pattern/     正式分类器、提示词、规则、taxonomy与原始样本
scripts/          当前推理入口和无需API的规则重放入口
tests/            离线测试；fixtures保存必要的历史提示词对照
data/             原始输入清单
outputs/
  interface_intent_attribution_step6_20261103/   历史基线与原始评分
  interface_semantic_freemium_20261120/          规则对照、失败提示词及重新运行证据
  interface_boundary_rules_20261120/            最新规则、87条结果与七条复读
  interface_gpt6_prompt_step4_20261029/          仅保留旧人工参照来源
docs/             整理记录及历史交接说明
```

两个历史实验中的`input_logs`是指向原始87条样本目录的相对符号链接，避免重复保存同一批对话。源代码快照、原始模型响应、预测和人工评分仍分别保留；不要覆盖历史实验文件。

## 安装与离线验证

使用Python 3.10及以上版本。

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m unittest discover -s tests
python scripts/replay_rules.py
```

离线测试和规则重放不会调用API。重放使用已保存的同一批模型答案，默认写入`outputs/local_replay/predictions.json`，并列出与保留结果不同的主路径编号；不读取人工标签或计算准确率。最新整理完成时81项离线测试通过。

## 对新输入调用模型

仅通过环境变量设置自己的`OPENAI_API_KEY`，不要把密钥写入仓库。然后运行：

```bash
python scripts/run_inference.py path/to/dialogue.txt --output outputs/local_inference/predictions.json
```

可传入多个文件；不传文件时使用原始87条。此命令会调用付费API。是否可使用配置中的模型，取决于自己的账户权限。输出新建在独立目录，不覆盖研究记录。

## 这次整理保留了什么

保留现行代码、81项测试、87条输入、旧新版人工参照、关键正负实验和可追溯证据。已从项目中清出较早的逐条分析汇总、重复压缩包、不完整尝试、临时锁、缓存和过时运行入口。完整清单见[文件整理记录](docs/文件整理记录_20261122.json)。本地备份位于项目外，不随仓库上传。

没有为原始对话或上游材料补授新许可证。历史交接资料仅作来源记录，现行实现和结果以本README及最新配置为准。
