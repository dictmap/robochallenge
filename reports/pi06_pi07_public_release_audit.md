# pi0.6 / pi0.7 公开复现性审计

## 结论

- 审计时间：`2026-06-03T03:41:39.274420Z`。
- 目前没有找到可直接复现的公开 `pi0.6` 或 `pi0.7` OpenPI checkpoint/config。
- 本地 OpenPI 仓库没有 `pi06/pi07/pi0.6/pi0.7` 训练或推理配置命中。
- `openpi-assets` 公共 bucket 常见 `pi06/pi07` 前缀对象数均为 0。
- `pi*0.6` 和 `pi0.7` 有公开论文/博客，但当前只能作为方法参考，不能按 `pi05_base` 那样下载权重并 smoke。

## 本地 OpenPI 扫描

- OpenPI root：`/home/yjl/robochallenge/openpi`。
- 扫描文件数：`113`。
- 命中数：`0`。

## 远端 OpenPI README 实时检查

- URL：`https://raw.githubusercontent.com/Physical-Intelligence/openpi/main/README.md`。
- 抓取成功：`True`。
- checkpoint 路径数：`10`。
- 预期公开基模路径均存在：`True`。
- pi0.6/pi0.7 checkpoint 路径数：`0`。

## pi0.7 官网页实时检查

- URL：`https://www.pi.website/pi07`。
- 抓取成功：`True`。
- 发布日期命中 2026-04-16：`True`。
- steerable 描述命中：`True`。
- checkpoint 路径数：`0`。

## 公共 GCS checkpoint 前缀

- 检查前缀数：`10`。
- 公开 checkpoint 是否命中：`False`。

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
- [pi0.7 blog](https://www.pi.website/pi07)：pi0.7 博客，发布于 2026-04-16，描述 steerable generalist 和组合泛化。
- [openpi issue 789](https://github.com/Physical-Intelligence/openpi/issues/789)：社区询问 pi0.6 是否会发布的公开 issue。
- [openpi issue 860](https://github.com/Physical-Intelligence/openpi/issues/860)：社区讨论 pi0.6 star 是否可从 pi0.5 checkpoint 实现的公开 issue。

## 对 RoboChallenge 的影响

- 当前可执行路线仍是：`pi05_base` -> Table30/Table30v2 数据适配 -> 任务 finetune/eval -> 官方提交入口。
- `pi*0.6` 可借鉴 RECAP 思路做后续优化，但需要奖励/成功标签、失败轨迹、干预数据或离线 RL 实现；不是一键换 checkpoint。
- `pi0.7` 可借鉴 steerable prompt、subtask、visual subgoal 和 metadata conditioning 思路；没有公开权重时不能声称复现模型本体。

## 边界

- 本审计只访问公开 OpenPI/GCS 资料，不接触 RoboChallenge 提交平台。
- 本审计不读取 token、submission id 或 checkpoint link，不上传、不下载 checkpoint 权重。
