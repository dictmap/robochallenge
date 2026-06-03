# Checkpoint 上传通道审计

## 结论

- 审计状态：`passed=True`。
- 是否执行上传：`False`。
- 是否读取明文凭据：`False`。
- 本地 tar 前置条件：`True`。
- tar 文件已存在：`False`；Git 忽略：`True`。
- runs 目录剩余空间：`464.579` GB。

## 本地命令可用性

- `hf`：available=`False`，version=``。
- `huggingface-cli`：available=`False`，version=``。
- `gh`：available=`False`，version=``。
- `git-lfs`：available=`True`，version=`git-lfs/3.0.2 (GitHub; linux amd64; go 1.18.1)`。
- `rclone`：available=`False`，version=``。
- `ossutil`：available=`False`，version=``。
- `aws`：available=`False`，version=``。
- `gsutil`：available=`False`，version=``。
- `gcloud`：available=`False`，version=``。
- `azcopy`：available=`False`，version=``。
- `curl`：available=`True`，version=`curl 7.81.0 (x86_64-pc-linux-gnu) libcurl/7.81.0 OpenSSL/3.0.2 zlib/1.2.11 brotli/1.0.9 zstd/1.4.8 libidn2/2.3.2 libpsl/0.21.0 (+libidn2/2.3.2) libssh/0.9.6/openssl/zlib nghttp2/1.43.0 librtmp/2.3 OpenLDAP/2.5.18`。

## 凭据迹象

- `huggingface`：env_present_count=`0`，config_file_present_count=`0`。
- `github_cli`：env_present_count=`0`，config_file_present_count=`0`。
- `rclone`：env_present_count=`0`，config_file_present_count=`0`。
- `aliyun_oss`：env_present_count=`0`，config_file_present_count=`0`。
- `aws_s3`：env_present_count=`0`，config_file_present_count=`0`。
- `google_cloud`：env_present_count=`0`，config_file_present_count=`0`。
- `azure_blob`：env_present_count=`0`，config_file_present_count=`0`。

## 候选上传通道

- `huggingface_hub`：tool_available=`False`，credential_hint_present=`False`，selected=`False`。
  - 阻塞：需要用户确认 Hugging Face 仓库、可见性、许可和 token 后才能上传。
- `github_release_or_lfs`：tool_available=`True`，credential_hint_present=`False`，selected=`False`。
  - 阻塞：需要用户确认 GitHub 资产大小限制、仓库策略和 token 后才能上传。
- `rclone_remote`：tool_available=`False`，credential_hint_present=`False`，selected=`False`。
  - 阻塞：需要用户指定 rclone remote 和可公开/评测端可访问路径。
- `object_storage`：tool_available=`False`，credential_hint_present=`False`，selected=`False`。
  - 阻塞：需要用户指定对象存储 bucket/path、访问权限和凭据。
- `manual_download`：tool_available=`True`，credential_hint_present=`False`，selected=`False`。
  - 阻塞：需要用户给出可由 RoboChallenge 评测端访问的下载 URL。

## 建议下一步

用户确认上传通道后，在 Linux 仓库根目录执行本地打包命令：

```bash
tar -C runs -cf runs/openpi_rtc_lora_materialized_policy_checkpoint.tar openpi_rtc_lora_materialized_policy_checkpoint
sha256sum runs/openpi_rtc_lora_materialized_policy_checkpoint.tar > runs/openpi_rtc_lora_materialized_policy_checkpoint.tar.sha256
```

## Blocking

- 需要用户选择上传通道和存储位置。
- 需要用户授权相应存储凭据；本审计只检查是否存在凭据迹象，不读取明文。
- 只有 LoRA/web checkpoint 路线需要生成真实 checkpoint link 后回填 RoboChallenge 网站。
- baseline 官方 ALOHA 路线不需要上传 checkpoint 或 checkpoint link。
- baseline 真实提交仍需要 ROBOCHALLENGE_SUBMISSION_TARGET_CONFIRMATION、ROBOCHALLENGE_USER_TOKEN、ROBOCHALLENGE_SUBMISSION_ID、ROBOCHALLENGE_SUBMISSION_VARIANT=baseline 和 ROBOCHALLENGE_REAL_RUN_CONFIRM。
