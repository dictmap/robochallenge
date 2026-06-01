# pi0.6 / pi0.7 公开复现性审计

## 结论

- 目前没有找到可直接复现的公开 `pi0.6` 或 `pi0.7` OpenPI checkpoint/config。
- 本地 OpenPI 仓库没有 `pi06/pi07/pi0.6/pi0.7` 训练或推理配置命中。
- `openpi-assets` 公共 bucket 常见 `pi06/pi07` 前缀对象数均为 0。
- `pi*0.6` 和 `pi0.7` 有公开论文/博客，但当前只能作为方法参考，不能按 `pi05_base` 那样下载权重并 smoke。

## 本地 OpenPI 扫描

- OpenPI root：`/home/yjl/robochallenge/openpi`。
- 扫描文件数：`113`。
- 命中数：`0`。

## 公共 GCS checkpoint 前缀

| prefix | object_count |
| --- | ---: |
| `checkpoints/pi06` | 0 |
| `checkpoints/pi07` | 0 |
| `checkpoints/pi0_6` | 0 |
| `checkpoints/pi0_7` | 0 |
| `checkpoints/pi06_base` | 0 |
| `checkpoints/pi07_base` | 0 |
| `checkpoints/pi0.6` | 0 |
| `checkpoints/pi0.7` | 0 |
| `checkpoints/pistar06` | 0 |
| `checkpoints/pi_star06` | 0 |

## 官方/公开资料

- [Physical-Intelligence/openpi](https://github.com/Physical-Intelligence/openpi)：公开 OpenPI 仓库当前列出的模型族为 pi0、pi0-FAST、pi0.5。
- [pi*0.6 paper](https://www.physicalintelligence.company/download/pistar06.pdf)：pi*0.6 / RECAP 论文，描述从经验和奖励反馈改进 VLA 的方法。
- [pi0.7 blog](https://www.pi.website/blog/pi07)：pi0.7 博客，发布于 2026-04-16，描述 steerable generalist 和组合泛化。
- [openpi issue 789](https://github.com/Physical-Intelligence/openpi/issues/789)：社区询问 pi0.6 是否会发布的公开 issue。
- [openpi issue 860](https://github.com/Physical-Intelligence/openpi/issues/860)：社区讨论 pi0.6 star 是否可从 pi0.5 checkpoint 实现的公开 issue。

## 对 RoboChallenge 的影响

- 当前可执行路线仍是：`pi05_base` -> Table30/Table30v2 数据适配 -> 任务 finetune/eval -> 官方提交入口。
- `pi*0.6` 可借鉴 RECAP 思路做后续优化，但需要奖励/成功标签、失败轨迹、干预数据或离线 RL 实现；不是一键换 checkpoint。
- `pi0.7` 可借鉴 steerable prompt、subtask、visual subgoal 和 metadata conditioning 思路；没有公开权重时不能声称复现模型本体。
