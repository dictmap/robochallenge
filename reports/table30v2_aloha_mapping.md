# Table30v2 ALOHA 最小分片字段映射

## 结论

- 官方 `convert_to_lerobot.py` 是单臂模板，不能直接用于当前 ALOHA 双臂分片。
- 当前可用最小分片是 `pack_the_toothbrush_holder`，包含 `left_states.jsonl`、`right_states.jsonl` 和三路视频。
- 数据本体是 14 维双臂状态/动作：左臂 7 维 + 右臂 7 维。
- OpenPI 配置 `cvpr_multitask_aloha_rtc` 使用 pi0.5，模型动作维度 `32`，训练/推理通过 padding 和输出截断桥接 14 维数据。
- checkpoint 的 `cvpr_multitask_aloha` norm stats 也是 14 维 `state/actions`，与该分片一致。

## 样例分片

- episode：`/home/yjl/yjl/RoboChallenge/baseline_pi05_multitask/20260413/aloha/pack_the_toothbrush_holder`
- task_info：`/home/yjl/yjl/RoboChallenge/datasets/Table30v2_extracted/pack_the_toothbrush_holder/meta/task_info.json`
- prompt：Put the toothbrush and toothpaste into the toiletries case in sequence, close the case, and then place it into the basket.
- task_tag：`['repeated', 'bimanual', 'manipulation', 'temporal', 'dual-arm', 'ALOHA']`

## 视频/状态长度

- left states：`1100`
- right states：`1100`
- cam_high_rgb.mp4: `1100` frames, `30.0` fps, `640x480`
- cam_left_wrist_rgb.mp4: `1100` frames, `30.0` fps, `640x480`
- cam_right_wrist_rgb.mp4: `1100` frames, `30.0` fps, `640x480`

## 字段维度

### left
- `ee_positions`: list dims `[7]`
- `effort`: list dims `[7]`
- `gripper_width`: `float`
- `joint_positions`: list dims `[6]`
- `joint_velocities`: list dims `[7]`
- `master_effort`: list dims `[7]`
- `master_qpos`: list dims `[7]`
- `qpos`: list dims `[6]`
- `timestamp`: `float`

### right
- `ee_positions`: list dims `[7]`
- `effort`: list dims `[7]`
- `gripper_width`: `float`
- `joint_positions`: list dims `[6]`
- `joint_velocities`: list dims `[7]`
- `master_effort`: list dims `[7]`
- `master_qpos`: list dims `[7]`
- `qpos`: list dims `[6]`
- `timestamp`: `float`

## 推荐映射

```json
{
  "raw_to_lerobot": {
    "observation/cam_high": "videos/cam_high_rgb.mp4 frame",
    "observation/cam_wrist_left": "videos/cam_left_wrist_rgb.mp4 frame",
    "observation/cam_wrist_right": "videos/cam_right_wrist_rgb.mp4 frame",
    "state": "concat(left.master_qpos[0:7], right.master_qpos[0:7]) -> 14",
    "action": "concat(left.master_qpos[t+1][0:7], right.master_qpos[t+1][0:7]) -> 14",
    "prompt/task": "Table30v2 task_info.task_desc.prompt"
  },
  "lerobot_to_openpi": {
    "repack": "LeRobotW1DualDataConfig + AlohaDualInputs expects observation/cam_high, observation/cam_wrist_left, observation/cam_wrist_right, state, actions/prompt",
    "model_padding": "14-dim state/action padded to pi0.5 model action_dim=32",
    "policy_output": "AlohaDualOutputs returns actions[:, :14]"
  }
}
```

## 下一步

- 写一个只处理该分片的 dry-run converter，不先写全量 LeRobot 数据，先验证 14 维 state/action 和三路图像键。
- converter 通过后再接 `LeRobotW1DualDataConfig(repo_id='cvpr_multitask_aloha')` 的训练/评测入口。
