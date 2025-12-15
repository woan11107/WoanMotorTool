# 电机调试工具使用说明

## 简介
这是一个用于电机调试的集成工具，支持扫描电机、设置ID、设置零点等功能。

## 功能特性
- [OK] 扫描总线上的所有电机
- [OK] 读取/设置电机ID和Master ID
- [OK] 设置单个或多个电机的零点位置
- [OK] 支持自定义串口配置（Linux/Windows通用）
- [OK] 配置持久化保存
- [OK] 中文界面

## 环境要求
- Python 3.7+
- pyserial >= 3.5
- numpy >= 1.21.0

## 安装依赖
```bash
pip install -r requirements.txt
```

## 使用方法

### 方式一：直接运行Python脚本
```bash
# Linux/macOS
python3 src/motor_tool.py

# Windows
python src/motor_tool.py
```

### 方式二：使用打包好的可执行文件

#### Linux/macOS
```bash
# 打包
chmod +x build_motor_tool.sh
./build_motor_tool.sh

# 运行
./dist/motor_tool
```

#### Windows
```cmd
REM 打包
build_motor_tool.bat

REM 运行
.\dist\motor_tool.exe
```

## 功能说明

### 1. 扫描电机
- 自动扫描总线上的所有电机
- 显示电机ID和Master ID
- 可自定义扫描范围

### 2. 读取电机ID和Master ID
- 读取指定电机的当前ID配置
- 不修改任何参数

### 3. 设置电机ID和Master ID
- 修改电机的CAN ID和Master ID
- **参数会永久保存到电机Flash中**
- 重新上电后配置不会丢失

### 4. 设置单个电机零点
- 将电机当前位置设置为零点
- 适用于单个电机的零点校准

### 5. 设置多个电机零点
- 批量设置多个电机的零点
- 支持用逗号或空格分隔ID列表

### 6. 查看/修改串口配置
- 修改串口端口（如 /dev/ttyACM1 或 COM3）
- 修改波特率（默认 921600）
- 修改最大扫描ID
- 配置保存在 motor_config.json 中

## 串口配置

### Linux
默认串口: `/dev/ttyACM1`
常见串口: `/dev/ttyACM0`, `/dev/ttyUSB0`, `/dev/ttyUSB1`

查看可用串口:
```bash
ls /dev/tty*
```

### Windows
默认串口: `COM3`
常见串口: `COM1`, `COM2`, `COM3`, 等

查看可用串口: 设备管理器 -> 端口(COM和LPT)

## 配置文件
配置文件 `motor_config.json` 包含以下设置:
```json
{
    "port": "/dev/ttyACM1",
    "baudrate": 921600,
    "max_scan_id": 16
}
```

## 注意事项

1. **权限问题 (Linux)**
   如果遇到串口权限错误，请执行:
   ```bash
   sudo usermod -a -G dialout $USER
   # 然后注销重新登录
   ```

2. **ID设置永久性**
   使用"设置电机ID和Master ID"功能后，新的ID会永久保存到电机的Flash中，重新上电不会丢失。

3. **零点设置**
   设置零点前确保电机已移动到期望的零点位置。

4. **电机供电**
   确保电机有足够的供电，仅USB供电可能无法正常工作。

## 故障排除

### 问题1: 找不到串口
- **Linux**: 检查串口设备是否存在 (`ls /dev/tty*`)
- **Windows**: 在设备管理器中查看COM端口号
- 确认USB线缆连接正常

### 问题2: 扫描不到电机
- 检查电机供电是否正常
- 检查串口波特率是否正确（默认921600）
- 检查CAN总线连接

### 问题3: 设置ID后重启又恢复
- 确保使用了"设置电机ID和Master ID"功能（会自动保存到Flash）
- 检查保存过程中是否有错误提示
- 确保设置过程中电机供电稳定

## 独立脚本使用

除了集成工具外，也可以单独使用各个功能脚本:

```bash
# 扫描电机
python3 scan_motors.py [串口] [最大ID]

# 读取ID
python3 set_id.py <电机ID>

# 设置ID
python3 set_id.py <当前ID> <新电机ID> <新MasterID>

# 设置单个电机零点
python3 set_zero.py <电机ID>

# 设置多个电机零点
python3 set_zero_all.py [电机ID1] [电机ID2] ...
```

## 版本信息
- 版本: v1.0
- 更新日期: 2025-12-10

## 技术支持
如有问题，请检查:
1. 串口配置是否正确
2. 电机供电是否正常
3. Python依赖是否完整安装
