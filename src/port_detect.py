#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
SLCAN 适配器自动识别

策略:正向识别 CANable,反向兜底 Damiao。
- 命中 CANable VID/PID 或 product 关键字 -> "canable"
- 端口存在但不命中 -> "damiao"
- 端口不存在 -> None
"""

import serial.tools.list_ports


CANABLE_VID_PID = [
    (0x16D0, 0x117E),
]

CANABLE_PRODUCT_KEYWORDS = ["canable"]


def _is_canable(info) -> bool:
    """根据 ListPortInfo 判断是否为 CANable 适配器"""
    vid = getattr(info, "vid", None)
    pid = getattr(info, "pid", None)
    if vid is not None and pid is not None and (vid, pid) in CANABLE_VID_PID:
        return True

    product = getattr(info, "product", None)
    if product:
        product_lower = product.lower()
        for kw in CANABLE_PRODUCT_KEYWORDS:
            if kw in product_lower:
                return True

    return False


def _safe_comports():
    """枚举串口,失败时返回空列表(永不抛异常)"""
    try:
        return list(serial.tools.list_ports.comports())
    except Exception:
        return []


def _is_usb_serial(info) -> bool:
    """识别是否为 USB-Serial 设备(过滤掉 Linux 内建的 /dev/ttyS* 等幽灵串口)"""
    return getattr(info, "vid", None) is not None


def detect_slcan_type(port: str):
    """
    根据指定端口判断协议类型。

    Returns:
        "canable" - 命中 CANable 特征
        "damiao"  - 端口存在但不是 CANable
        None      - 端口不在系统串口列表中
    """
    if not port:
        return None

    for info in _safe_comports():
        if getattr(info, "device", None) == port:
            return "canable" if _is_canable(info) else "damiao"

    return None


def pick_default_port():
    """
    自动挑选一个可用 USB-Serial 端口。

    优先选 CANable;否则选第一个 USB-Serial 当 Damiao。
    内建 /dev/ttyS* 等非 USB 端口会被过滤掉,避免在没插适配器时误选。

    Returns:
        (device, slcan_type) 元组,或 None(没有任何 USB-Serial 串口)
    """
    ports = [info for info in _safe_comports() if _is_usb_serial(info)]
    if not ports:
        return None

    for info in ports:
        if _is_canable(info):
            device = getattr(info, "device", None)
            if device:
                return device, "canable"

    for info in ports:
        device = getattr(info, "device", None)
        if device:
            return device, "damiao"

    return None
