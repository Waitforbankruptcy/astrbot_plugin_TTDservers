
#调用标准库
import socket #网络通信
import struct #数据打包和解包
import sys    #命令行参数
"""
协议：OpenTTDGameProtocol (TCP协议)
请求：PACKET_CLIENT_GAME_INFO (类型 7)
响应：PACKET_SERVER_GAME_INFO (类型 6)
"""

"""
定义用户ip识别函数
识别以下：
ipv4
ipv6
域名
"""

def server_ip(ipduanko):#第一轮检查

    #首先检查只有一个参数
    if len(ipduanko) != 1:
        print("输入存在错误\n"
              "请输入ip地址\n"
              "示例：\n"
              "IPv4:TTD 127.0.0.0:3979\n"
              "IPv6:TTD [::1]:3979\n"
              "(注：兼容域名)")
        #报错
        return None, None #最后返回空
    """
    首先确保带端口：检查关键字符{:}
    再检查是否是ip或域名的其中一种:检查ip或域名
    检查方法：
    ipv6：检查存在关键字符: {[},{]} (ipv6的括号)
    ipv4：检查存在关键字符: {.}X3 (ipv4的3个点)
    域名：无法通过上面检查且检查存在关键字符: {.}>0 (每个域用一个点分开,至少一个点)
    """
    #将第一轮的结果赋到第二轮分类检查的函数中
    csip = ipduanko[0]
    #先检查是否是ipv6，再检查是否带端口，再检查是否属于域名,ipv4这两类,
    if csip.startswith('['): #检查第一个字符是否是关键字符{[}
        zd = csip.rfind(']:')
        if zd !=-1 : #从前面往后检查查看是否有关键字符{]}和{:}
            ip =csip[1:zd] #截取ip
            try:
                port = int(csip[zd + 2:]) #截取端口并取整，识别端口是否为全数字
            except ValueError:
                print(f"无效IPv6地址：{csip}(非法端口)\nIPv6示例:[::1]:3979")
                return None, None#报错直接返回空
            if port<0 or port > 65535: #检查端口数值是否超标
                print(f"无效IPv6地址：{csip}(非法端口)\nIPv6示例:[::1]:3979")
                return None, None#报错直接返回空
            return ip, port#返回ip和端口
        print(f"无效IPv6地址：{csip}(非法IPv6地址)\nIPv6示例:[::1]:3979")
        return None, None#报错直接返回空
    #ipv4/域名
    if ':' not in csip: #识别是否带有关键字符{:},没有则直接报错
        print("输入存在错误\n"
              "请输入ip地址\n"
              "示例：\n"
              "IPv4:TTD 127.0.0.0:3979\n"
              "IPv6:TTD [::1]:3979\n"
              "(注：兼容域名)")
        return None, None #报错直接返回空
    ip,ipv4_ym_port = csip.split(':',1)
    if not ip: #确保ip不是莫名其妙的值
        print("输入存在错误\n"
              "请输入ip地址\n"
              "示例：\n"
              "IPv4:TTD 127.0.0.0:3979\n"
              "IPv6:TTD [::1]:3979\n"
              "(注：兼容域名)")
        return None, None #报错直接返回空
    try:
        port = int(ipv4_ym_port) #截取端口并取整，识别端口是否为全数字
    except ValueError:
        print(f"无效IPv4地址：{csip}(非法端口)\nIPv4:TTD 127.0.0.0:3979")
        return None, None#报错直接返回空
    if port<0 or port > 65535: #检查端口数值是否超标
        print(f"无效IPv4地址：{csip}(非法端口)\nIPv4:TTD 127.0.0.0:3979")
        return None, None#报错直接返回空
    return ip, port #返回ip和端口
"""
连接
ip
端口
先域名解析
"""
def ttd_tup(ip,port,timeout=60):
    try:#域名
        ymjx = socket.getaddrinfo(ip, port,
            socket.AF_UNSPEC,     # 不限地址族,IPv4 IPv6
            socket.SOCK_STREAM)   # tcp协议
    except socket.gaierror as e: #域名解析爆掉出现的
        return None #报错返回空
    cuowu = None #记录
    #开始连接
    for family, socktype, proto, _, sockaddr in ymjx:
        """
        把ymjx里的值分别赋给对应变量
        地址族:socket.AF_UNSPEC->family
        套接字类型:socket.SOCK_STREAM->socktype
        套接字地址:ip:pory->sockaddr
        协议号：proto
        """
        socket1 = socket.socket(family,socktype,proto) #IPv4 和 IPv6 的地址族不同，用不同的 socket
        socket1.settimeout(timeout) #超时时间/秒

        #握手
        try:
            socket1.connect(sockaddr)#对地址发起链接
            request = struct.pack('<HB', 3, 7)
            """
            把数据打包到变量request
            总长度是 3 字节，类型是 7
            struct.pack 格式字符串 
            '<HB':'<'小端序（OpenTTD 全线使用小端序）
            'H'unsigned short，2 字节 → 长度字段
            'B'unsigned char，1 字节 → 类型字段
            """
            socket1.sendall(request) #发送request至服务器
            socket1.settimeout(10) #接收超时时间为10秒
            ysdata = [] #存放拼接完成的数据
            while True: #死循环用于接受数据
                try:
                    data = socket1.recv(4096) #设置接受数据的列表，最多接受4096字节
                    if not data: #如果返回为空则服务器已关闭连接
                        break #服务器关闭连接直接跳出循环
                    ysdata.append(data)
                    #将每次接受到的数据都填充到ysdata里
                    ys = b''.join(ysdata)
                    if len(ys) >=2:
                    #识别原始数据字节长度,前2个字节是包的总长度字段，所以至少收到 2 字节才能解读
                        datalen = struct.unpack_from('<H', ys, 0)[0]
                        #识别和解包数据前2字节,确定包总长度
                        if len(ys) >= datalen: #核实数据长度
                            break #如果核实成功跳出循环，开始数据解包
                except socket.timeout:  #如果数据接收超时则说明服务器炸或者网络爆
                    break #接收失败，跳出循环
            ttddata = b''.join(ysdata)#
            """
            不管成功与否都将ysdata列表里的数据按顺序直接拼接
            完成后赋值给ttddata，现在ttddata里面的就是服务器发送过来的原始数据
            """
            return ttddata
        except Exception as e:
            """
            当前地址失败（服爆了）
            记录错误，继续尝试下一个地址
            """
            cuowu = e
        finally:
            socket1.close() # 管你三七二十一直接关闭当前 socket，释放资源
    return None #所有地址都爆了返回空
"""
解析原始数据
"""

def rq(date):
    #把天数转换成年月日。
    year = date // 360
    rem = date % 360
    month = rem // 30 + 1
    day = rem % 30 + 1
    return year, month, day
LANDSCAPE_NAMES = {
    0: "温带",
    1: "亚寒带",
    2: "热带",
    3: "玩具",
}


def game_data(data):#解析
    if len(data) <3:#数据至少3字节，否则报错
        return None#报错返回空
    jmbata = data[2]#读取data列表里第3个字节
    if jmbata !=6: #查看数据包类型是否符合
        return None#报错返回空
    #如果正常则进行解码
    hbata = data[3:] #获得3个字节以后剩余字节
    off = 0 #当前读取偏移量

    def read(n):#检查函数
        nonlocal off
        if off + n > len(hbata): #读取剩下的数据检查·是否完整
            raise ValueError(f"查询错误，缺少{len(hbata) - off}数据")
        v = hbata[off:off + n]
        off += n
        return v

    def u_8():
        #读 1 字节无符号整数
        return read(1)[0]

    def u_16():
        #读 2 字节无符号整数(小端序)
        return struct.unpack('<H', read(2))[0]

    def u_32():
        #读 4 字节无符号整数(小端序)
        return struct.unpack('<I', read(4))[0]

    def u_64():
        #读 8 字节无符号整数(小端序)
        return struct.unpack('<Q', read(8))[0]
    def s():
        nonlocal off
        start = off
        # 向后扫描直到遇到 null 或缓冲区结束
        while off < len(hbata) and hbata[off] != 0:
            off += 1
        # 提取 [start, off) 之间的内容并解码
        val = hbata[start:off].decode('utf-8', errors='replace')
        # 跳过 null 字节本身
        off += 1
        return val
    #解包
    info = {}
    try:
        #版本号
        ver = u_8()
        #版本 >= 7
        if ver >= 7:
            ticks = u_64()
            # 换算成可读时长：74 tick ≈ 1 秒
            total_seconds = ticks / 74
            hours = int(total_seconds // 3600)
            minutes = int((total_seconds % 3600) // 60)
            info['游戏运行时长'] = f"{hours} 小时 {minutes} 分钟"
        #版本 >= 6
        if ver >= 6:
            u_8()
        #版本 >= 5
        if ver >= 5:
            u_32()
            info['游戏脚本名称'] = s()
        #版本 >= 4
        if ver >= 4:
            grf_count = u_8()
            info['NewGRF数量'] = grf_count
            grfs = []
            for _ in range(grf_count):
                grfid = u_32()
                md5 = read(16).hex()
                name = s()
                grfs.append(f"{name} ")
            info['NewGRF列表'] = grfs
        # 版本 >= 3
        # 游戏内日历日期和起始日期，原始值是"天数"，
        # 用 rq 转换成可读的年月日。
        if ver >= 3:
            cal_date = u_32()
            cal_start = u_32()
            y1, m1, d1 = rq(cal_date)
            y2, m2, d2 = rq(cal_start)
            info['游戏当前日期'] = f"{y1} 年 {m1} 月 {d1} 日"
            info['游戏起始日期'] = f"{y2} 年 {m2} 月 {d2} 日"
        #版本 >= 2
        if ver >= 2:
            info['最大公司数'] = u_8()
            info['当前公司数'] = u_8()
            u_8()
        # 基础字段
        info['服务器名称'] = s()
        s()
        info['是否需要密码'] = "是" if u_8() else "否"
        info['最大客户端数'] = u_8()
        info['当前在线客户端数'] = u_8()
        info['当前观察者数'] = u_8()
        info['地图宽度'] = u_16()
        info['地图高度'] = u_16()
        landscape = u_8()
        info['景观类型'] = LANDSCAPE_NAMES.get(landscape, f"未知({landscape})")
        info['是否专用服务器'] = "是" if u_8() else "否"
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
def format_game_info(ttddata):
    """把原始字节组装成可读文本，返回字符串。"""
    lines = []
    if ttddata:
        info = game_data(ttddata)
        if info:
            lines.append("  服务器信息:")
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
    ip, port = server_ip([target])
    if ip is None or port is None:
        return (
            "地址格式错误。\n"
            "示例：\n"
            "  IPv4：TTD 127.0.0.1:3979\n"
            "  IPv6：TTD [::1]:3979\n")
    ttddata = ttd_tup(ip, port)
    return format_game_info(ttddata)

if __name__ == "__main__":
    # 独立运行时：python TTDTCP.py ip:port
    target = sys.argv[1] if len(sys.argv) > 1 else ""
    print(query(target))






