from abc import ABC, abstractmethod # 抽象基类实现多种串口兼容
import time

class SlcanProtocolBase(ABC):
    """
    SLCAN 协议抽象基类
    所有 CAN 传输层必须实现这三个接口
    """

    def __init__(self, serial_port):
        self.serial = serial_port

    @abstractmethod
    def init(self):
        """
        初始化 CAN 设备
        """
        pass

    @abstractmethod
    def send(self, frame_id: int, data: bytes) -> bool:
        """
        发送一帧 CAN 数据
        :param frame_id: CAN ID
        :param data: 最多 8 字节
        """
        pass

    @abstractmethod
    def recv(self):
        """
        接收一帧 CAN 数据
        :return: (can_id:int, payload:bytes) 或 None
        """
        pass

class CanableSlcan(SlcanProtocolBase):
    """
    MKS CANable / candleLight / slcan ASCII 协议
    """

    def init(self):
        # 给 USB 虚拟串口一点稳定时间
        time.sleep(0.1)

        # 关闭通道，防止未知状态
        self.serial.write(b'C\r')
        time.sleep(0.05)

        # 设置波特率
        # S6 = 500k, S8 = 1M
        self.serial.write(b'S8\r')
        time.sleep(0.05)

        # 打开通道
        self.serial.write(b'O\r')
        time.sleep(0.05)

        # 清空回显
        self.serial.reset_input_buffer()

        print("[SLCAN] CANable initialized")

    def send(self, frame_id: int, data: bytes) -> bool:
        try:
            data = data[:8]
            data_hex = "".join(f"{b:02X}" for b in data)

            # 标准帧 t + 3位ID + len + data
            cmd = f"t{frame_id:03X}{len(data)}{data_hex}\r"
            self.serial.write(cmd.encode("ascii"))
            return True
        except Exception:
            return False

    def recv(self):
        try:
            raw = self.serial.read_until(b'\r')
            if not raw:
                return None

            line = raw.decode("ascii", errors="ignore").strip()
            if not line:
                return None

            # 标准帧
            if line[0] == 't':
                can_id = int(line[1:4], 16)
                payload = bytes.fromhex(line[5:])
                return can_id, payload

            # 扩展帧（一般用不到，留着兜底）
            if line[0] == 'T':
                can_id = int(line[1:9], 16)
                payload = bytes.fromhex(line[10:])
                return can_id, payload

            return None

        except Exception:
            return None

class DamiaoSlcan(SlcanProtocolBase):
    """
    达妙 USB-CAN 私有二进制协议
    """

    SEND_TEMPLATE = bytearray([
        0x55, 0xAA, 0x1E, 0x03, 0x01, 0x00, 0x00, 0x00,
        0x0A, 0x00, 0x00, 0x00, 0x00,
        0x00, 0x00,          # CAN ID (L, H)
        0x00, 0x00, 0x00, 0x08, 0x00, 0x00,
        0x00, 0x00, 0x00, 0x00,
        0x00, 0x00, 0x00, 0x00,
        0x00
    ])

    FRAME_LEN = 16
    HEADER = 0xAA
    TAIL = 0x55

    def init(self):
        # 达妙模块一般不需要额外配置
        print("[SLCAN] Damiao initialized")

    def send(self, frame_id: int, data: bytes) -> bool:
        try:
            frame = bytearray(self.SEND_TEMPLATE)

            frame[13] = frame_id & 0xFF
            frame[14] = (frame_id >> 8) & 0xFF

            data = data[:8]
            frame[21:21 + len(data)] = data

            self.serial.write(frame)
            return True

        except Exception:
            return False

    def recv(self):
        """
        这里保留最小实现
        实际完整解析你可以后续直接搬你原来的代码
        """
        try:
            if self.serial.in_waiting < self.FRAME_LEN:
                return None

            buf = self.serial.read(self.FRAME_LEN)
            if buf[0] != self.HEADER or buf[-1] != self.TAIL:
                return None

            can_id = buf[3] | (buf[4] << 8)
            payload = buf[7:15]

            return can_id, payload

        except Exception:
            return None
