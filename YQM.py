import socket #TCP连接库
import struct #打包解包
import sys #读取命令
"""
邀请码获得
"""
def chax(xingxi): # 查询并过滤信息函数
    newgrf_lookup.clear()  #每次查询清空全局表，防止混乱爆了
    sock = socket.create_connection((gcdizhi, gcduanko), timeout=30) #地址和端口，超时30秒
    try:
        payload = struct.pack("<BB", gcxybanb, wangluoxieybanb) #NetworkGameInfo版本
        payload += zfcbm("15.0") #给与客户端版本字符串
        payload += struct.pack("<I", 0)
        sock.sendall(tcpsjb(qqgklb, payload))#类型为CLIENT_LISTING
        result = None
        while True:
            ptype, payload = jsbao(sock) #接收数据包，解码类型和数据
            if ptype == GC: # 如果是有问题的包
                return None  # 直接炸 返回空
            elif ptype == laqvgrfyingsuobiao:#如果是NewGRF的索引表包
                count = struct.unpack("<H",payload[4:6])[0] #那就开始按小端序解包
                off = 6
                for _ in range(count):#按顺序全部NewGRF都要
                    idx = struct.unpack("<I",payload[off:off+4])[0] #解
                    off += 4
                    off += 4 #不要的grfid直接扔
                    off += 16 #不用的md5也是，直接扔
                    name, off = duqvzifc(payload, off) #传进当前偏移量
                    newgrf_lookup[idx] = name #存表
            elif ptype == fanhuifwqlbiao: #如果是服务器列表包
                count = struct.unpack("<H",payload[0:2])[0] #直接按小端序解欸
                if count == 0: #如果是0
                    break # 直接跳
                off = 2
                for _ in range(count): #按顺序全部检查
                    conn_str, off = duqvzifc(payload, off) #传入当前偏移量
                    info, off = lianjiebianma(payload, off)
                    if conn_str == xingxi:# 找到邀请码一样的
                        result = info #保存结果
        return result
    finally: #管什么问题都执行一遍
        sock.close() #关闭连接

def zfcbm(s):
    return s.encode("utf-8") + b"\x00" #设置UTF-8字节，追加\0结束符
def tcpsjb(ptype,payload=b""): #数据包
    #小端序H = uint16 总长，B = uint8 类型
    #总长度=2+1+剩下，2为长度标识，1为类型
    return struct.pack("<HB", 2 + 1 + len(payload),ptype) + payload
def jiesho(sock,n):
    huancn = b"" #初始化
    while len(huancn) < n: #循环接受字节
        shengqv = sock.recv(n - len(huancn)) #读取剩余的
        if not shengqv: #如果获得是空的
            raise ConnectionError("连接关闭") #连接出问题直接爆
        huancn += shengqv #读取数据到缓冲的地方
    return huancn #返回数据
def jsbao(sock): #接受包
    #识别前面两字符识别包长度
    zongcjma = struct.unpack("<H", jiesho(sock,2))[0]
    data = jiesho(sock,zongcjma - 2) #重新识别除开头两字符以后的字符，即类型+剩下数据
    return data[0],data[1:] #返回数据,第一个类型以及后面的所有
def duqvzifc(data, off): #读取字节串
    duq = data.find(b"\x00", off) # 从off开始寻找\0
    if duq == -1: #如果找不到结束符\0
        raise ValueError("字符串无终止") #直接爆
    return data[off:duq].decode("utf-8", errors="replace"), duq + 1
def rq(date): #计算时间
    year = date // 360
    rem = date % 360
    month = rem // 30 + 1
    day = rem % 30 + 1
    return year, month, day
def lianjiebianma(data, off):
    def u_8(): #内部函数：读取1字节无符号整数
        nonlocal off #声明off为外层函数的局部变量
        v = data[off]
        off += 1
        return v
    def u_16():
        nonlocal off
        v = struct.unpack("<H",data[off:off+2])[0] #切片取2字节
        off += 2
        return v
    def u_32():
        nonlocal off
        v = struct.unpack("<I",data[off:off+4])[0] #切片取4字节
        off += 4
        return v
    def u_64():
        nonlocal off
        v = struct.unpack("<Q",data[off:off+8])[0] #切片取8字节
        off += 8
        return v
    def s():
        nonlocal off
        v, off = duqvzifc(data, off)
        return v
    info = {} #初始化，放结果
    ver = u_8()
    if ver >= 7: #如果版本 >= 7
        ticks = u_64()
        sec = ticks // 74
        info["游戏运行时长"] = f"{sec//3600} 小时 {(sec%3600)//60} 分钟"
    newgrf_ser = u_8() if ver >= 6 else 0
    if ver >= 5:  #如果版本 >= 5
        u_32()
        info["游戏脚本名称"] = s()
    if ver >= 4:#如果版本 >= 4
        grf_count = u_8()
        info["NewGRF数量"] = grf_count #保存NewGRF数量
        grfs = []  #清空列表，放NewGRF名
        for _ in range(grf_count):
            if newgrf_ser == 2: #如果是LookupId模式
                idx = u_32()
                name = newgrf_lookup.get(idx, "") #从全局表查名字，查不到就用空字符串
                grfs.append(f"{name} ") #将名字加空格后追加到列表
            elif newgrf_ser == 1:
                u_32() #不需要grfid，无视
                off += 16 #不需要md5，无视
                name = s() #读取名字字符串
                grfs.append(f"{name} ")  #将名字加空格后追加到列表
            else:
                u_32() #不需要grfid，无视
                off += 16 #不需要md5，无视
        info["NewGRF列表"] = grfs #保存NewGRF名
    if ver >= 3:  #如果版本 >= 3
        cd = u_32()
        cs = u_32()
        y1, m1, d1 = rq(cd)
        y2, m2, d2 = rq(cs)
        info["游戏当前日期"] = f"{y1} 年 {m1} 月 {d1} 日"
        info["游戏起始日期"] = f"{y2} 年 {m2} 月 {d2} 日"
    if ver >= 2: #如果版本 >= 2
        info["最大公司数"] = u_8()
        info["当前公司数"] = u_8()
        u_8()
    info["服务器名称"] = s()
    info["服务器版本"] = s()
    if ver < 6:#如果版本 < 6
        u_8()
    info["是否需要密码"] = "是" if u_8() else "否"
    info["最大客户端数"] = u_8()
    info["当前在线客户端数"] = u_8()
    info["当前观察者数"] = u_8()
    if ver < 3: #如果版本 < 3
        u_16()
        u_16()
    if ver < 6: #如果版本 < 6
        while u_8() != 0: #遇到\0就跳
            pass
    info["地图宽度"] = u_16()
    info["地图高度"] = u_16()
    info["景观类型"] = LANDSCAPE_NAMES.get(u_8(), "未知")
    info["是否专用服务器"] = "是" if u_8() else "否"
    return info, off #返回解析结果

gcdizhi = "coordinator.openttd.org" #GC_HOST GC 官方主机名
gcduanko = 3976 #GC_PORT GC TCP 监听端口
gcxybanb = 6 #GC_VERSION GC 协议版本（NETWORK_COORDINATOR_VERSION）
wangluoxieybanb = 7 #NETWORK_GAME_INFO_VERSION NetworkGameInfo 协议版本
GC= 0    #GC_ERROR  GC 返回错误
fwqzhuce = 1 #SERVER_REGISTER 服务器注册 无用
zhuceqr = 2 #GC_REGISTER_ACK 注册确认 无用
fwqzhuangtgx = 3 #SERVER_UPDATE 服务器状态更新 无用
qqgklb = 4 #CLIENT_LISTING 客户端请求公开服务器列表
fanhuifwqlbiao= 5 #GC_LISTING GC 返回服务器列表
qqyqmlj= 6 #CLIENT_CONNECT 客户端请求通过邀请码连接 无用
fengpeilp= 7 #GC_CONNECTING GC 分配令牌 无用
ljsb= 8 #SERCLI_CONNECT_FAILED 连接失败 无用
fqlj= 9 #GC_CONNECT_FAILED GC 放弃连接 无用
khdtzylianje= 10 #CLIENT_CONNECTED 客户端通知 GC 已连接 无用
zhilian= 11 #GC_DIRECT_CONNECT GC 指示直连 无用
qingqstunno= 12 #GC_STUN_REQUEST GC 请求 STUN 无用
stunjieguo= 13 #SERCLI_STUN_RESULT STUN 结果 无用
stunlianjie= 14 #GC_STUN_CONNECT GC 指示 STUN 连接 无用
laqvgrfyingsuobiao= 15 #GC_NEWGRF_LOOKUP GC NewGRF索引表
zhishiturnzhongxv= 16 #GC_TURN_CONNECT GC 指示 TURN 中继 无用
newgrf_lookup = {}   #空字典存NewGRF名字
LANDSCAPE_NAMES = {0: "温带", 1: "亚寒带", 2: "热带", 3: "玩具"}
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
def shuchu(info, yqm): #输出
    lines = []
    if not info: #如果没有解析到信息
        return "查询失败。" #爆了的话
    lines.append("  服务器信息:")
    lines.append(f"  服务器邀请码: {yqm}")
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

    return "\n".join(lines)
def query(target: str) -> str:
    target = (target or "").strip()#防止输入奇奇怪怪的东西导致爆了
    if not target: #没有值的话
        return (
            "请输入服务器邀请码。\n"
            "示例：+abcd1234"
        )
    try: #检查
        info = chax(target)
    except Exception as e:#爆了的话
        return f"查询出错：{e}" #返回爆的错
    return shuchu(info, target)  #清空并返回结果
def main(): #定义主函数
    target = sys.argv[1].strip() if len(sys.argv) > 1 else ""
    print(query(target)) #打印结果
if __name__ == "__main__":
    main()