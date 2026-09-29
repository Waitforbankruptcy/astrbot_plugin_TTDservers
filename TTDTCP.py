
#调用标准库
import socket #网络通信
import struct #数据打包和解包
import sys    #命令行参数
"""
协议：OpenTTDGameProtocol (TCP协议)
请求：PACKET_CLIENT_GAME_INFO (类型 7)
响应：PACKET_SERVER_GAME_INFO (类型 6)
"""

#其他函数
LANDSCAPE_NAMES = {
    0: "温带",
    1: "亚寒带",
    2: "热带",
    3: "玩具",
}


def rq(date):
    #把天数转换成年月日。
    year = date // 360
    rem = date % 360
    month = rem // 30 + 1
    day = rem % 30 + 1
    return year, month, day


#ip识别
def server_csip(input): #命令参数 主要为ipv6和ipv4
    """
    ipv4：127.0.0.0:3979
    ipv6:[::1]:3979
    """
    if len(input) != 1:#识别指令是否只有一个参数
       print(f"错误，请输入ip地址，示例：\n IPv4:TTD 127.0.0.0:3979 \n IPv6:[::1]:3979 \n(注：兼容ipv6以及域名)")
       return None, None #报错直接返回空

    csip = input[0]
    #ipv6
    if csip.startswith('['):#识别第一个字符是否为ipv6的[，是则使用ipv6的方法，不是则返回至ipv4
        end = csip.find(']')#有[则开始寻找ipv6的]，确保是完整ipv6地址
        if end  == -1:#如果没有找到]则直接报错
            print(f"无效IPv6地址：{csip}，IPv6示例:[::1]:3979")
            return None, None #报错直接返回空
        #通过ipv6识别则直接开始一下操作
        ip = csip[1:end]#删除括号并识别ip（原来写成了 input[1:end]，那是列表，会崩）
        ipv6_hobufen = csip[end+1:]#剩下冒号和端口
        if not ipv6_hobufen.startswith(':'):#确保后面格式正常，不然直接打回，省的报其他什么垃圾错
            print(f"无效IPv6地址：{csip}，IPv6示例:[::1]:3979")
            return None, None #报错直接返回空
        try:
            port = int(ipv6_hobufen[1:])#识别端口
        except ValueError:#识别端口是否正常，省的又报错
            print(f"无效IPv6地址：{csip}，IPv6示例:[::1]:3979")
            return None, None #报错直接返回空
        return ip,port #返回ip和端口
    #ipv4
    if ':' not in csip:#识别ipv4格式是否正确，不然直接报错给他看
        print(f"无效IPv4地址：{csip}，IPv4:TTD 127.0.0.0:3979")
        return None, None #报错直接返回空
    ip, ipv4_hobufen = csip.rsplit(':', 1)#把ip单独拎出来
    if not ip:#确保用户给的ip的格式是正确的，不然直接爆给它看
        print(f"无效IPv4地址：{csip}，IPv4:TTD 127.0.0.0:3979")
        return None, None #报错直接返回空
    try:
        port = int(ipv4_hobufen)#直接取整确保端口是数字而不是什么奇奇怪怪的东西
    except ValueError: #不是数字直接爆！！！
        print(f"无效IPv4地址：{csip}，IPv4:TTD 127.0.0.0:3979")
        return None, None #报错直接返回空
    return ip, port #返回ip和端口


#连接
def ttd_tup(ip,port,timeout=60): #ip=服务器ip,port=端口,timeout=连接时间/秒
    """
    开始连接
    ip
    端口
    整个过程静默，不打印中间日志
    """
    try:#先搞域名
        addr_list = socket.getaddrinfo(ip, port,
                 socket.AF_UNSPEC,     # 不限地址族,IPv4 IPv6我都要！！！
                 socket.SOCK_STREAM)   # TCP 协议
    except socket.gaierror as e:#域名解析爆掉出现的
        return None #报错直接返回空

    last_err = None #记个错
    #连接地址
    for family, socktype, proto, _, sockaddr in addr_list:
        sock = socket.socket(family, socktype, proto)#IPv4 和 IPv6 的地址族不同，用不同的 socket。
        sock.settimeout(timeout)  # 连接超时

    #开始正式连接
        try:
            sock.connect(sockaddr)
            request = struct.pack('<HB', 3, 7)#struct.pack 格式字符串 '<HB':'<'小端序（OpenTTD 全线使用小端序）'H'unsigned short，2 字节 → 长度字段'B'unsigned char，1 字节 → 类型字段
            sock.sendall(request)
            sock.settimeout(10)  # 接收超时单独设为 10 秒
            chunks = []         # 收集所有收到的数据
            while True:
                try:
                    data = sock.recv(4096) #接受数据
                    if not data:
                        # recv 返回空 bytes 表示服务器已关闭连接
                        break
                    chunks.append(data)# 解析头，判断是否已收完
                    raw = b''.join(chunks)
                    if len(raw) >= 2:# 前 2 字节是小端序的包总长度
                        pkt_len = struct.unpack_from('<H', raw, 0)[0]
                        if len(raw) >= pkt_len:# 已收到完整数据，停止接收
                            break
                except socket.timeout:
                    break# 等待数据超时，服务器炸

            # 合并数据 bytes 对象返回
            raw = b''.join(chunks)
            return raw

        except Exception as e:
            # 当前地址失败（服爆了）
            # 记录错误，继续尝试下一个地址
            last_err = e
        finally:
            sock.close()# 管你三七二十一直接关闭当前 socket，释放资源

    # 所有地址都爆了
    return None


def parse_game_info(data):#解析

    if len(data) < 3:# 至少需要 3 字节
            return None

    # 解析
    pkt_type = data[2]
    if pkt_type != 6:
        return None

    # 跳过 3 字节包头，
    buf = data[3:]
    off = 0  # 当前读取偏移量

    def read(n):
        nonlocal off
        if off + n > len(buf):
            raise ValueError(f"服务器爆了: 需要 {n}, 剩余 {len(buf) - off}")
        v = buf[off:off + n]
        off += n
        return v

    def u8():
        """读 1 字节无符号整数"""
        return read(1)[0]

    def u16():
        """读 2 字节无符号整数（小端序）"""
        return struct.unpack('<H', read(2))[0]

    def u32():
        """读 4 字节无符号整数（小端序）"""
        return struct.unpack('<I', read(4))[0]

    def u64():
        """读 8 字节无符号整数（小端序）"""
        return struct.unpack('<Q', read(8))[0]

    def s():
        nonlocal off
        start = off
        # 向后扫描直到遇到 null 或缓冲区结束
        while off < len(buf) and buf[off] != 0:
            off += 1
        # 提取 [start, off) 之间的内容并解码
        val = buf[start:off].decode('utf-8', errors='replace')
        # 跳过 null 字节本身
        off += 1
        return val

    info = {}
    try:
        #版本号
        ver = u8()
        #版本 >= 7
        if ver >= 7:
            ticks = u64()
            # 换算成可读时长：74 tick ≈ 1 秒
            total_seconds = ticks / 74
            hours = int(total_seconds // 3600)
            minutes = int((total_seconds % 3600) // 60)
            info['游戏运行时长'] = f"{hours} 小时 {minutes} 分钟"
        #版本 >= 6
        if ver >= 6:
            u8()
        #版本 >= 5
        if ver >= 5:
            u32()
            info['游戏脚本名称'] = s()
        #版本 >= 4
        if ver >= 4:
            grf_count = u8()
            info['NewGRF数量'] = grf_count
            grfs = []
            for _ in range(grf_count):
                grfid = u32()
                md5 = read(16).hex()
                name = s()
                grfs.append(f"{name} ")
            info['NewGRF列表'] = grfs
        # 版本 >= 3
        # 游戏内日历日期和起始日期，原始值是"天数"，
        # 用 rq 转换成可读的年月日。
        if ver >= 3:
            cal_date = u32()
            cal_start = u32()
            y1, m1, d1 = rq(cal_date)
            y2, m2, d2 = rq(cal_start)
            info['游戏当前日期'] = f"{y1} 年 {m1} 月 {d1} 日"
            info['游戏起始日期'] = f"{y2} 年 {m2} 月 {d2} 日"
        #版本 >= 2
        if ver >= 2:
            info['最大公司数'] = u8()
            info['当前公司数'] = u8()
            u8()
        # 基础字段
        info['服务器名称'] = s()
        s()
        info['是否需要密码'] = "是" if u8() else "否"
        info['最大客户端数'] = u8()
        info['当前在线客户端数'] = u8()
        info['当前观察者数'] = u8()
        info['地图宽度'] = u16()
        info['地图高度'] = u16()
        landscape = u8()
        info['景观类型'] = LANDSCAPE_NAMES.get(landscape, f"未知({landscape})")
        info['是否专用服务器'] = "是" if u8() else "否"
    except (ValueError, IndexError) as e:
        return info
    return info


DISPLAY_ORDER = [
    "服务器名称",
    "服务器版本",
    "是否需要密码",
    "当前在线客户端数",
    "最大客户端数",
    "当前观察者数",
    "当前公司数",
    "最大公司数",
    "地图宽度",
    "地图高度",
    "景观类型",
    "游戏起始日期",
    "游戏当前日期",
    "游戏运行时长",
    "游戏脚本名称",
    "是否专用服务器",
    "NewGRF数量",
    "NewGRF列表",
]


def format_game_info(raw):
    """把原始字节组装成可读文本，返回字符串。"""
    lines = []
    if raw:
        info = parse_game_info(raw)
        if info:
            lines.append("服务器信息:")
            printed = set()
            for key in DISPLAY_ORDER:
                if key in info:
                    v = info[key]
                    if isinstance(v, list):
                        if not v:
                            lines.append(f"  {key}: []")
                        else:
                            lines.append(f"  {key}:")
                            for item in v:
                                lines.append(f"  {item}")
                    else:
                        lines.append(f"  {key}: {v}")
                    printed.add(key)
            for key, v in info.items():
                if key in printed:
                    continue
                if isinstance(v, list):
                    if not v:
                        lines.append(f"  {key}: []")
                    else:
                        lines.append(f"  {key}:")
                        for item in v:
                            lines.append(f"  {item}")
                else:
                    lines.append(f"  {key}: {v}")
        else:
            lines.append("解析失败。")
    else:
        lines.append("查询失败。")
    return "\n".join(lines)
def query(target: str) -> str:
    ip, port = server_csip([target])
    if ip is None or port is None:
        return (
            "地址格式错误。\n"
            "示例：\n"
            "  IPv4：TTD 127.0.0.1:3979\n"
            "  IPv6：TTD [::1]:3979\n"
            "  域名：TTD example.com:3979"
        )
    raw = ttd_tup(ip, port)
    return format_game_info(raw)



if __name__ == "__main__":
    # 独立运行时：python TTDTCP.py ip:port
    target = sys.argv[1] if len(sys.argv) > 1 else ""
    print(query(target))