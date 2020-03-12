# -*- coding: utf-8 -*-
# author:jeffrycheng
# project:network_build_automation
# date:2020-03-05

import datetime,xlrd,xlwt,sys,copy,time,re,os
from prettytable import PrettyTable




#接口前缀了带宽字典
interface_prefix = {'100':'H','25':'TF','40':'FG','10':'T','400':'FH','1':'G'}

#表格格式
style = xlwt.XFStyle()
al = xlwt.Alignment()
al.horz = 0x02
al.vert = 0x01
style.alignment = al
font = xlwt.Font()
font.name = 'title'
font.bold = True
style.font = font
borders = xlwt.Borders()
borders.left = xlwt.Borders.THIN
borders.right = xlwt.Borders.THIN
borders.top = xlwt.Borders.THIN
borders.bottom = xlwt.Borders.THIN
borders.left_colour = 0x40
borders.right_colour = 0x40
borders.top_colour = 0x40
borders.bottom_colour = 0x40
style.borders = borders
pattern = xlwt.Pattern()
pattern.pattern = xlwt.Pattern.SOLID_PATTERN
pattern.pattern_fore_colour = 5
style.pattern = pattern
style1 = xlwt.XFStyle()
al = xlwt.Alignment()
al.horz = 0x02
al.vert = 0x01
style1.alignment = al
font = xlwt.Font()
font.name = 'paper'
font.bold = True
style1.font = font
borders = xlwt.Borders()
borders.left = xlwt.Borders.THIN
borders.right = xlwt.Borders.THIN
borders.top = xlwt.Borders.THIN
borders.bottom = xlwt.Borders.THIN
borders.left_colour = 0x40
borders.right_colour = 0x40
borders.top_colour = 0x40
borders.bottom_colour = 0x40
style1.borders = borders




#功能区排序
def nsort(nlist):
    n = len(nlist)
    for i in range(n):
        for j in range(0, n-i-1):
            if int(re.findall(r'\d+',nlist[j])[0]) > int(re.findall(r'\d+',nlist[j+1])[0]):
                nlist[j], nlist[j + 1] = nlist[j + 1], nlist[j]
            elif int(re.findall(r'\d+',nlist[j])[0]) == int(re.findall(r'\d+',nlist[j+1])[0]):
                if int(re.findall(r'\d+',nlist[j])[1]) > int(re.findall(r'\d+',nlist[j+1])[1]):
                    nlist[j], nlist[j + 1] = nlist[j + 1], nlist[j]
    return nlist

#槽位排序
def psort(plist):
    n = len(plist)
    for i in range(n):
        for j in range(0, n-i-1):
            if int(''.join(re.findall(r'\d+',plist[j]))) > int(''.join(re.findall(r'\d+',plist[j+1]))):
                plist[j], plist[j + 1] = plist[j + 1], plist[j]
    return plist

#获取所有编号
def getnum(num_str):
    num_list = []
    try:
        for ns in num_str.split(','):
            if len(ns.split('-')) == 2:
                num_list += range(int(ns.split('-')[0]),int(ns.split('-')[1])+1)
            else:
                num_list.append(ns.split('-')[0])
        num_list = [ str(i) for i in sorted(list(set([ int(nl) for nl in num_list ])))]
    except:
        num_list = []
    return num_list




def build_hardware(project_name):
    #获取架构规划信息，生成虚拟连接关系
    device_roles = {}
    data = xlrd.open_workbook("arch.xlsx")
    table = data.sheets()[0]
    for i in range(1, table.nrows):
        role_name = table.row_values(i)[0]
        role_num = table.row_values(i)[1]
        table1 = data.sheet_by_name(role_name)
        port_list = []
        port_role_dict = {}
        for j in range(table1.nrows):
            port_list += table1.row_values(j)
        port_list = [i for i in port_list if i]
        port_roles = list(set([i.split('-')[1] for i in port_list]))
        for port_role in port_roles:
            port_role_list = nsort([ i for i in set(port_list) if port_role in i])
            port_role_dict[port_role] = port_role_list
        device_roles[role_name] = {'role_num': role_num, 'port_role': port_role_dict}
    link_table = []
    for device_role,v in device_roles.items():
        local_device_list = [ device_role+'-'+str(i) for i in range(1,int(v['role_num'])+1) ]
        for peer_role,role_ports in v['port_role'].items():
            conn_table = []
            if peer_role == device_role:
                for n in [2 * i for i in range(len(local_device_list)/2)]:
                    for role_port in role_ports:
                        conn_table.append([local_device_list[n], role_port, local_device_list[n + 1], role_port])
                link_table += conn_table
                continue
            if peer_role in device_roles.keys():
                peer_role_num = device_roles.get(peer_role).get('role_num')
                peer_device_list = [ peer_role+'-'+str(i) for i in range(1,int(peer_role_num)+1) ]
                peer_ports = device_roles.get(peer_role).get('port_role').get(device_role)
                del device_roles[peer_role]['port_role'][device_role]
            else:
                peer_device_list = [ i.split('-')[1]+'-'+i.split('-')[0] for i in role_ports ]
                peer_ports = [ '' for i in range(len(local_device_list)*len(role_ports)/len(peer_device_list))]
            port_length = len(role_ports)/len(peer_device_list)
            port_length = 1 if port_length == 0 else port_length
            for local_device in local_device_list:
                for role_port in role_ports:
                    conn_table.append([local_device,role_port,'',''])
            n = 0
            m = 1
            plist = []
            for i in range(len(peer_ports)):
                plist.append(i)
                m += 1
                if m > port_length:
                    for j in plist:
                        for peer_device in peer_device_list:
                            conn_table[n][2] = peer_device
                            conn_table[n][3] = peer_ports[j]
                            n += 1
                    m = 1
                    plist = []
            link_table += conn_table
    #获取端口映射关系，生成物理连接关系
    data = xlrd.open_workbook("port_map.xlsx")
    sheet_names = data.sheet_names()
    port_map = {}
    for sheet_name in sheet_names:
        table = data.sheet_by_name(sheet_name)
        port_map_dict = {}
        for i in range(1,table.nrows):
            map_list = table.row_values(i)
            port_map_dict[map_list[0]] = {
                'port_name':map_list[1],
                'bandwidth':str(int(map_list[2])),
                'physical_name':interface_prefix.get(str(int(map_list[2])))+map_list[1]
            }
        port_map[sheet_name] = port_map_dict
    for lk in link_table:
        for device_role in  port_map.keys():
            if device_role == lk[0].split('-')[0]:
            #if device_role == re.search(r'[a-z]+',lk[0],re.I).group():
                lk[1] = port_map.get(device_role).get(lk[1]).get('physical_name')
            if device_role == lk[2].split('-')[0]:
                #if device_role == re.search(r'[a-z]+',lk[2],re.I).group():
                lk[3] = port_map.get(device_role).get(lk[3]).get('physical_name')
    #读取设备硬件信息
    data = xlrd.open_workbook("hardware_info.xlsx")
    sheet_names = data.sheet_names()
    device_hardware = {}
    for sheet_name in sheet_names:
        device_hardware_dict = {}
        table = data.sheet_by_name(sheet_name)
        for i in range(1,table.nrows):
            device_hardware_list = table.row_values(i)
            if device_hardware_list[0] == 'module':
                key = interface_prefix.get(str(int(device_hardware_list[3])))+device_hardware_list[1]
            else:
                key = device_hardware_list[1]
            try:
                device_hardware_dict[device_hardware_list[0]][key] = device_hardware_list[2]
            except:
                device_hardware_dict[device_hardware_list[0]] = {}
                device_hardware_dict[device_hardware_list[0]][key] = device_hardware_list[2]
        device_hardware[sheet_name] = device_hardware_dict
    # 根据建设数量生成最终连接关系,并获取设备名称
    os.chdir(project_name)
    data = xlrd.open_workbook("var.xlsx")
    table = data.sheet_by_index(0)
    region = ''
    datacenter_name = ''
    for i in range(1,table.nrows):
        row = table.row_values(i)
        if row[0] == 'region':
            region = row[2]
        elif row[0] == 'datacenter_name':
            datacenter_name = row[2]
    data = xlrd.open_workbook("build.xlsx")
    table = data.sheet_by_name('order')
    device_list = []
    all_device_list = []
    for i in range(1,table.nrows):
        if table.row_values(i)[0] in device_roles.keys():
            device_list += [table.row_values(i)[0]+'-'+j for j in getnum(table.row_values(i)[1])]
        all_device_list += [table.row_values(i)[0] + '-' + j for j in getnum(table.row_values(i)[1])]
    last_link_table = []
    for lk in link_table:
        if lk[0] not in all_device_list or lk[2] not in all_device_list:
            continue
        else:
            last_link_table.append(lk)
    table = data.sheet_by_name('location')
    device_name_dict = {}
    for i in range(1,table.nrows):
        row = table.row_values(i)
        device_name_dict[row[0]] = "%s-%s-%s-%s-%s"%(
            region,
            datacenter_name,
            row[1],
            device_hardware.get(row[0].split('-')[0]).get('chassis').values()[0],
            row[0]
        )
    #根据连接关系生成采购清单和安装方案
    device_port_dict = {}
    for i in last_link_table:
        if i[0] in device_list:
            try:
                device_port_dict[i[0]].append(i[1])
            except:
                device_port_dict[i[0]] = [i[1]]
        if i[2] in device_list:
            try:
                device_port_dict[i[2]].append(i[3])
            except:
                device_port_dict[i[2]] = [i[3]]
    device_hardware_dict = {}
    for device in device_list:
        role = device.split('-')[0]
        device_hardware_dict[device] = {}
        for k,v in device_hardware[role].items():
            if k != 'module' and k != 'linecard':
                device_hardware_dict[device][k] = device_hardware[role][k]
        device_hardware_dict[device]['module'] = {}
        for i in device_port_dict.get(device):
            device_hardware_dict[device]['module'][i] = device_hardware[role]['module'][i]
        device_hardware_dict[device]['linecard'] = {}
        if device_hardware.get(role).get('linecard'):
            for i in device_port_dict.get(device):
                index1 = re.search(r'\d+',i.split('/')[0]).group()
                index2 = index1+'/'+i.split('/')[1]
                if index1 in device_hardware.get(role).get('linecard').keys():
                    device_hardware_dict[device]['linecard'][index1] = device_hardware.get(role).get('linecard').get(index1)
                if index2 in device_hardware.get(role).get('linecard'):
                    device_hardware_dict[device]['linecard'][index2] = device_hardware.get(role).get('linecard').get(index2)
    order_dict = {}
    for v in device_hardware_dict.values():
        for device_type,device_dict in v.items():
            if device_dict:
                try:
                    order_dict[device_type] += device_dict.values()
                except:
                    order_dict[device_type] = device_dict.values()
    #输出连接关系、物料信息和采购清单
    global style
    f = xlwt.Workbook()
    sheet1 = f.add_sheet(u'物料清单', cell_overwrite_ok=True)
    row0 = [u'型号', u'类型', u'数量']
    for i in range(0, len(row0)):
        sheet1.write(0, i, row0[i], style)
        sheet1.col(i).width = 3500
    order_list = []
    for device_type,v in order_dict.items():
        order_list += [ [i,device_type,str(v.count(i))] for i in list(set(v)) ]
    n = 1
    for i in order_list:
        sheet1.write(n, 0, i[0], style1)
        sheet1.write(n, 1, i[1], style1)
        sheet1.write(n, 2, i[2], style1)
        n += 1
    sheet2 = f.add_sheet(u'连接关系', cell_overwrite_ok=True)
    row1 = [u'连接类型', u'本端设备', u'本端设备端口', u'对端设备', u'对端设备接口']
    for i in range(0, len(row1)):
        sheet2.write(0, i, row1[i], style)
        sheet2.col(i).width = 3500
    n = 1
    for i in last_link_table:
        link_type = i[0].split('-')[0]+'-'+i[2].split('-')[0]
        local_device_name = device_name_dict.get(i[0]) if device_name_dict.get(i[0]) else i[0]
        local_port = i[1]
        peer_device_name = device_name_dict.get(i[2]) if device_name_dict.get(i[2]) else i[2]
        peer_port = i[3]
        sheet2.write(n, 0, link_type, style1)
        sheet2.write(n, 1, local_device_name, style1)
        sheet2.write(n, 2, local_port, style1)
        sheet2.write(n, 3, peer_device_name, style1)
        sheet2.write(n, 4, peer_port, style1)
        n +=1
    sheet3 = f.add_sheet(u'物料安装表', cell_overwrite_ok=True)
    row2 = [u'设备', u'物料', u'类型', u'槽位']
    for i in range(0, len(row2)):
        sheet3.write(0, i, row2[i], style)
        sheet3.col(i).width = 3500
    n = 1
    for device in device_list:
        device_name = device_name_dict.get(device) if device_name_dict.get(device) else device
        for k,v in device_hardware_dict.get(device).items():
            if v:
                device_type = k
                for x,y in v.items():
                    slot_numer = x
                    device_model = y
                    sheet3.write(n, 0, device_name, style1)
                    sheet3.write(n, 1, device_model, style1)
                    sheet3.write(n, 2, device_type, style1)
                    sheet3.write(n, 3, slot_numer, style1)
                    n += 1
    filename = 'order_scheme_%s.xls' % time.strftime('%Y-%m-%d-%H-%M', time.localtime(time.time()))
    f.save(filename)
    os.chdir('..')
    return device_roles,device_list,last_link_table,device_name_dict






