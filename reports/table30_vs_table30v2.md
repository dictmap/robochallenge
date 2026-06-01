# Table30 与 Table30v2 数据差异审计

## 结论

- `Table30` 和 `Table30v2` 是两个不同数据集，不能混用任务名、机器人形态或 checkpoint。
- 用户给出的 `benchmark_detail` 页面更接近原始 Table30 榜单语境；RoboChallenge `challenges` 页面另有 `Table 30 V2 （CVPR Competition Benchmark）`，公开榜单里出现 `pi0.5/rc_baseline`。
- 当前 Linux 本地已有的是 Table30v2 资料和 baseline，不是 Table30 原版全量资料。
- 当前 ALOHA checkpoint 名称为 `table30v2_multitask_baseline_aloha`，应标注为 Table30v2 baseline；不能直接声称它复现了 Table30 原榜单。

## 数据集入口

| 项 | Table30 | Table30v2 |
| --- | --- | --- |
| Hugging Face | `RoboChallenge/Table30` | `RoboChallenge/Table30v2` |
| 本地 API 快照 | `sources/hf_table30_api.json` | `sources/hf_table30v2_api.json` |
| 本地 README | `baseline/official_table30_readme.md` | `baseline/official_table30v2_readme.md` |
| Linux 本地数据 | 未发现原版 Table30 目录 | `datasets/Table30v2`、`datasets/Table30v2_extracted` |
| 当前 baseline | 未发现 Table30 专用 checkpoint | `table30v2_multitask_baseline_aloha` |

## 机器人形态差异

| 数据集 | 机器人形态 |
| --- | --- |
| Table30 | ARX5、UR5、FRANKA、ALOHA |
| Table30v2 | ARX5、UR5、ALOHA、DOS-W1 |

关键差异：Table30 有 `FRANKA`，Table30v2 用 `DOS-W1/W1` 替代了 FRANKA 口径。现有 `demo.py/test.py` 支持 `dosw`、`aloha`、`arx5`、`ur5`，说明它是 Table30v2/CVPR baseline 口径。

## 任务命名差异

Table30 示例任务名：

- `arrange_fruits_in_basket`
- `clean_dining_table`
- `fold_dishcloth`
- `hang_toothbrush_cup`
- `make_vegetarian_sandwich`
- `open_the_drawer`
- `scan_QR_code`
- `sweep_the_rubbish`

Table30v2 示例任务名：

- `arrange_fruits`
- `fold_the_clothes`
- `hang_the_cup`
- `pack_the_toothbrush_holder`
- `place_objects_into_desk_drawer`
- `sweep_the_trash`
- `wipe_the_blackboard`
- `item_classification`

这些不是简单版本号替换，任务命名和语义都有变化；提交前必须以目标 benchmark 的任务列表为准。

## 对当前复现路线的影响

1. 当前 Notebook 和 `run_aloha_mock_smoke.sh` 只能证明 Table30v2 ALOHA baseline 链路可复现。
2. 如果目标是 Table30 原榜单，需要补齐 Table30 数据、Table30 对应模型/配置，或确认官方是否允许用 Table30v2 baseline 作为 Table30 提交入口。
3. 如果目标是 Table30v2/CVPR Competition，可以继续沿现有 `baseline_pi05_multitask`、`demo.py` 和 `test.py` 推进。
4. 报告和 README 必须显式写 `Table30v2 baseline`，避免误报为 Table30。
