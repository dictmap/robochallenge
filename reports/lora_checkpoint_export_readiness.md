# LoRA checkpoint 导出就绪审计

## 结论

- 本地导出就绪：`True`。
- 网站提交就绪：`False`。
- checkpoint 目录：`runs/openpi_rtc_lora_materialized_policy_checkpoint`。
- 文件数量：`18`；目录数量：`6`；总大小：`11.06 GB`。
- 参数数据 shard 数量：`13`。
- Git 忽略状态：`True`。
- tar stream smoke：attempted=`True`，passed=`True`。

## 必需文件

- `runs/openpi_rtc_lora_materialized_policy_checkpoint/params/_METADATA`：exists=`True`，size=`27.68 KB`。
- `runs/openpi_rtc_lora_materialized_policy_checkpoint/params/_CHECKPOINT_METADATA`：exists=`True`，size=`258.00 B`。
- `runs/openpi_rtc_lora_materialized_policy_checkpoint/params/manifest.ocdbt`：exists=`True`，size=`118.00 B`。
- `runs/openpi_rtc_lora_materialized_policy_checkpoint/params/ocdbt.process_0/manifest.ocdbt`：exists=`True`，size=`539.00 B`。
- `runs/openpi_rtc_lora_materialized_policy_checkpoint/assets/cvpr_multitask_aloha/norm_stats.json`：exists=`True`，size=`3.37 KB`。

## 最大文件抽样

- `params/ocdbt.process_0/d/c230cdef20308244d8966b0378828d28`：`2.33 GB`。
- `params/ocdbt.process_0/d/0f9a64a5e24d82eab428ba2d781a631c`：`2.33 GB`。
- `params/ocdbt.process_0/d/ea0eb1da0b1de430d7b9540e7446e9cc`：`2.09 GB`。
- `params/ocdbt.process_0/d/ea277db0c77abb39d8748fad4dbdd60f`：`1.82 GB`。
- `params/ocdbt.process_0/d/5047410dcf11cdce9de44cfb044a0fe7`：`1.18 GB`。
- `params/ocdbt.process_0/d/d9e48255aa77ab30ba91b7dadddedd62`：`795.72 MB`。
- `params/ocdbt.process_0/d/f6a9cd18b93097e1b73f86ca8e3858fa`：`333.74 MB`。
- `params/ocdbt.process_0/d/f159d091fe1d1b4d3b69f71cbd8557c6`：`138.23 MB`。
- `params/ocdbt.process_0/d/42a081e7991955a76ae1b67d122f30f7`：`90.62 MB`。
- `params/_METADATA`：`27.68 KB`。
- `params/ocdbt.process_0/d/aad9216614f8c61b4a9d5c180807e9f4`：`3.60 KB`。
- `assets/cvpr_multitask_aloha/norm_stats.json`：`3.37 KB`。

## tar stream smoke

- 命令：`set -o pipefail; tar -C /home/yjl/robochallenge/repo/runs -cf - openpi_rtc_lora_materialized_policy_checkpoint | wc -c`。
- 结果：attempted=`True`，passed=`True`，耗时 `19.666` 秒。
- archive stream bytes：`11879987200`；expected min bytes：`11879949503`。

## 建议导出命令

默认不自动打包大文件。需要上传 checkpoint 时，在 Linux 仓库根目录手动执行：

```bash
tar -C runs -cf runs/openpi_rtc_lora_materialized_policy_checkpoint.tar openpi_rtc_lora_materialized_policy_checkpoint
sha256sum runs/openpi_rtc_lora_materialized_policy_checkpoint.tar > runs/openpi_rtc_lora_materialized_policy_checkpoint.tar.sha256
```

生成的 `.tar` 文件被 `.gitignore` 排除，不应提交到 Git。

## Blocking

- 需要用户选择并授权可公开或评测端可访问的存储位置。
- 需要用户提供真实 ROBOCHALLENGE_USER_TOKEN。
- 需要用户提供真实 ROBOCHALLENGE_SUBMISSION_ID。
- 上传后需要把真实 checkpoint link 填回 RoboChallenge 网站；本脚本不会伪造链接。
