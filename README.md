# 电机调试工具 使用说明

## 简介
本仓库提供一个用于达妙（或兼容协议）电机调试的命令行工具集合，功能包括：扫描电机、读取/设置电机 CAN ID 和 Master ID、设置单个或批量零点、以及串口配置管理。工具以 `src/` 目录下的 Python 脚本为主。

## 主要特性
- 扫描总线上的电机并读取 Master ID
- 修改电机 CAN ID 与 Master ID（写入后保存到电机 Flash）
- 设置单个或多个电机的零点
- 串口配置持久化（`motor_config.json`）
- 支持 Linux 和 Windows（默认串口在 Windows 下为 `COM3`）

## 环境与依赖
- Python 3.7+
- 依赖见 `requirements.txt`（包含 `pyserial`, `numpy`, `colorama`）

安装依赖:
```bash
pip install -r requirements.txt
```

## 快速开始

1. 克隆或切换到项目目录:
```bash
cd /path/to/MotorToolPy
```
2. 编辑或检查 `motor_config.json`（可选）以设置默认串口和波特率。默认内容示例：
```json
{
    "port": "/dev/ttyACM0",
    "baudrate": 921600,
    "max_scan_id": 16
}
```
3. 运行主程序（交互式菜单）:
```bash
# Linux / macOS
python3 src/motor_tool.py

# Windows
python src/motor_tool.py
```

## 脚本说明与用法
工具主要脚本位于 `src/` 下：

- `src/motor_tool.py`：集成的交互式主程序，包含串口配置、扫描、设置ID、设置零点等菜单。
- `src/scan_motors.py`：扫描指定 ID 范围内的电机并读取 Master ID。
- `src/set_id.py`：读取或设置单个电机的 CAN ID / Master ID。
- `src/set_zero.py`：设置单个电机的零点。
- `src/set_zero_all.py`：对指定的一组电机批量设置零点。

常用命令行用法：
```bash
# 扫描电机: 可选参数 <串口> <最大ID> <波特率>
python3 src/scan_motors.py [/dev/ttyACM0] [16] [921600]

# 读取ID
python3 src/set_id.py <电机ID>

# 设置ID（示例：将当前ID为1的电机设置为新ID 2）
python3 src/set_id.py 1 2
# 如果不提供 new_master_id，脚本会自动计算 new_master_id = 0x10 + new_motor_id

# 设置单个电机零点
python3 src/set_zero.py <电机ID>

# 批量设置零点（传入要设置的ID列表）
python3 src/set_zero_all.py 1 2 3 4
```

## 默认配置说明
- 默认串口（Linux）: `/dev/ttyACM0`（代码 `DEFAULT_CONFIG`）
- Windows 启动时默认会切换为 `COM3`
- 默认波特率: `921600`
- 默认扫描最大 ID: `16`

请以 `src/motor_tool.py` 中的 `motor_config.json` 为准，或在程序内通过“查看/修改串口配置”菜单更新并保存。

## 注意事项

- 权限（Linux）: 若遇到串口权限问题，可将用户加入 `dialout` 组：
```bash
sudo usermod -a -G dialout $USER
# 注销后重新登录以使组变更生效
```
- 写入 ID 操作会将参数保存到电机 Flash，确保写入过程中电机供电稳定。
- 设置零点前应把电机移动到期望零点位置再执行零点命令。

## 常见故障与排查

- 无法打开串口：确认串口设备路径存在（Linux: `/dev/tty*`；Windows: 设备管理器查看 COM 端口），并检查是否被其它程序占用。
- 扫描不到电机：检查电机供电、总线连接和波特率（默认 921600）。
- 设置 ID 后不生效：确认写入过程无报错，且电机在写入时有稳定供电。

## 文件与实现要点（供开发者参考）
- 串口/转CAN 协议相关逻辑位于 `src/interface.py`，包含 `MotorController`、`Motor`、`ArmManager` 等类。
- 扫描逻辑会基于 `MotorController.refresh_status()` 与 `read_master_id()` 来判断设备存在性并获取 Master ID。

## 版本信息
- 版本: v1.2
- 更新日期: 2025-12-15

---

如需我把 README 翻译成英文、生成更详细的使用示例，或把此 README 用作 PyPI/项目主页的 README，我可以继续帮忙完善。
