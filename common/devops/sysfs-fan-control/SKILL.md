---
name: sysfs-fan-control
description: 凡需读写 /sys/class/hwmon 下的风扇 PWM、温度源或阈值文件（nct6775 / nct6798 等），即当加载。
---

# sysfs 风扇控制之律

## 先 ls 后写

Linux sysfs 是内核驱动的运行时窗口，**不存在即不可用**。写脚本前必先 `ls <目录>/` 确认真实文件名，不得凭文档臆造。

- 教训：`nct6775` 驱动并无 `pwmX_stop` 文件。该驱动里最低 PWM 由 `pwmX_floor` 控制，`pwmX_stop_time` 是停转延迟（毫秒），不是 PWM 值。凭文档臆造 `pwmX_stop` 属严重错误。
- 必须逐一确认存在后方可写入：`pwmX_enable`（控制模式）、`pwmX_target_temp`、`pwmX_temp_tolerance`、`pwmX_start`、`pwmX_floor`、`pwmX_step_up_time` / `pwmX_step_down_time`、`pwmX_stop_time`。

## 温度源先读标签

写 `pwmX_temp_sel` 前先 `cat temp[N]_label` 确认各传感器身份（CPUTIN、SYSTIN、AUXTIN 等），勿猜索引含义。

## 写入前后对比

写前先 `cat` 各文件当前值，写后再次读取验证生效，并确认无权限报错。

## 单位

`target_temp` 用毫摄氏度（`45000` = 45°C），`temp_tolerance` 亦然（`2000` = ±2°C），`step_up_time` / `step_down_time` 用毫秒。
