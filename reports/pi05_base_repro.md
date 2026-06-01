# pi0.5 基模复现记录

## 结论

- 官方基模路径：`gs://openpi-assets/checkpoints/pi05_base`。
- 公共 GCS 对象数：`29`，总大小约 `11.587 GiB`。
- 本地缓存路径：`/home/yjl/.cache/openpi/openpi-assets/checkpoints/pi05_base`。
- 当前已匹配大小：`11.587 GiB`。
- 下载开关 `DOWNLOAD_PI05_BASE=0`，并行数 `DOWNLOAD_JOBS=1`，参数加载开关 `LOAD_PI05_PARAMS=0`。

## 配置核对

### pi05_libero

- model：`Pi0Config`，`pi05=True`。
- action_dim：`32`，action_horizon：`10`。
- data：`LeRobotLiberoDataConfig`，repo_id：`physical-intelligence/libero`。
- weight_loader：`CheckpointWeightLoader(params_path='gs://openpi-assets/checkpoints/pi05_base/params')`。

### pi05_aloha_pen_uncap

- model：`Pi0Config`，`pi05=True`。
- action_dim：`32`，action_horizon：`50`。
- data：`LeRobotAlohaDataConfig`，repo_id：`physical-intelligence/aloha_pen_uncap_diverse`。
- weight_loader：`CheckpointWeightLoader(params_path='gs://openpi-assets/checkpoints/pi05_base/params')`。

### pi05_full_droid_finetune

- model：`Pi0Config`，`pi05=True`。
- action_dim：`32`，action_horizon：`16`。
- data：`RLDSDroidDataConfig`，repo_id：`droid`。
- weight_loader：`CheckpointWeightLoader(params_path='gs://openpi-assets/checkpoints/pi05_base/params')`。

### pi05_droid_finetune

- model：`Pi0Config`，`pi05=True`。
- action_dim：`32`，action_horizon：`16`。
- data：`LeRobotDROIDDataConfig`，repo_id：`your_hf_username/my_droid_dataset`。
- weight_loader：`CheckpointWeightLoader(params_path='gs://openpi-assets/checkpoints/pi05_droid/params')`。

## 说明

- `pi05_base` 是 Fine-Tuning 基模，不是 RoboChallenge 可直接提交的任务 policy。
- 对 RoboChallenge 提交仍需要在该基模或官方 Table30v2 baseline 上接数据、任务配置和评测入口。
- 真实提交需要用户提供 RoboChallenge 网站的 `user_token` 和 `submission_id`。

- 本次为轻量探测，下面的参数加载 smoke 来自此前已通过的同一缓存状态。

## 参数加载 smoke

```json
{
  "loaded": true,
  "seconds": 4.11,
  "leaf_count": 51,
  "total_elements": 3353433872,
  "first_shapes": [
    {
      "shape": [
        1152
      ],
      "dtype": "bfloat16"
    },
    {
      "shape": [
        1152
      ],
      "dtype": "bfloat16"
    },
    {
      "shape": [
        27,
        1152
      ],
      "dtype": "bfloat16"
    },
    {
      "shape": [
        27,
        1152
      ],
      "dtype": "bfloat16"
    },
    {
      "shape": [
        27,
        1152
      ],
      "dtype": "bfloat16"
    },
    {
      "shape": [
        27,
        1152
      ],
      "dtype": "bfloat16"
    },
    {
      "shape": [
        27,
        4304
      ],
      "dtype": "bfloat16"
    },
    {
      "shape": [
        27,
        1152,
        4304
      ],
      "dtype": "bfloat16"
    },
    {
      "shape": [
        27,
        1152
      ],
      "dtype": "bfloat16"
    },
    {
      "shape": [
        27,
        4304,
        1152
      ],
      "dtype": "bfloat16"
    },
    {
      "shape": [
        27,
        16,
        72
      ],
      "dtype": "bfloat16"
    },
    {
      "shape": [
        27,
        1152,
        16,
        72
      ],
      "dtype": "bfloat16"
    },
    {
      "shape": [
        27,
        1152
      ],
      "dtype": "bfloat16"
    },
    {
      "shape": [
        27,
        16,
        72,
        1152
      ],
      "dtype": "bfloat16"
    },
    {
      "shape": [
        27,
        16,
        72
      ],
      "dtype": "bfloat16"
    },
    {
      "shape": [
        27,
        1152,
        16,
        72
      ],
      "dtype": "bfloat16"
    },
    {
      "shape": [
        27,
        16,
        72
      ],
      "dtype": "bfloat16"
    },
    {
      "shape": [
        27,
        1152,
        16,
        72
      ],
      "dtype": "bfloat16"
    },
    {
      "shape": [
        1152
      ],
      "dtype": "bfloat16"
    },
    {
      "shape": [
        14,
        14,
        3,
        1152
      ],
      "dtype": "bfloat16"
    }
  ]
}
```
