# -*- coding: utf-8 -*-
# author:jeffrycheng
# project:network_build_automation
# date:2020-03-03

from jinja2 import Environment,FileSystemLoader
import os,xlrd,ipaddress,gol


#获取反掩码
def convert_mask(mask):
    b = (int(mask) * "1") + ((32 - int(mask)) * "0")
    b = [int(x, 2) for x in (b[:8],b[8:16],b[16:24],b[24:])]
    mask2 = "%s.%s.%s.%s" % tuple(b)
    reverse_mask = '.'.join([str(255-int(x)) for x in mask2.split('.')])
    return reverse_mask

#默认加载ip裂解表
def load_address_mask(project_name):
    address_mask_dict = {}
    try:
        data = xlrd.open_workbook("%s/address.xlsx"%project_name)
        for table in data.sheets():
            try:
                if table.row_values(0)[6] == u'device_name' and table.row_values(0)[7] == u'port_name':
                    for i in range(len(table.col_values(6)[1:])):
                        device_name_list = table.col_values(6)[1:][i].split(';')
                        port_name = table.col_values(7)[1:][i]
                        for device_name in device_name_list:
                            address_mask = table.col_values(8)[1:][i] + '/' + str(table.col_values(4)[1:][i]).strip('.0')
                            if address_mask_dict.get(device_name+port_name):
                                address_mask_dict[device_name+port_name].append(address_mask)
                            else:
                                address_mask_dict[device_name + port_name] = [address_mask]
            except:
                continue
        return address_mask_dict
    except:
        return address_mask_dict

#加载建设变量
def load_var(project_name):
    var_dict = {}
    try:
        data = xlrd.open_workbook("%s/var.xlsx"%project_name)
        table = data.sheets()[0]
        var_list = table.col_values(0)[1:]
        for i in range(len(var_list)):
            var_name = var_list[i]
            var_type = table.col_values(1)[i+1]
            var_value = table.col_values(2)[i+1]
            if var_type == 'str':
                var_value = str(var_value)
            elif var_type == 'int':
                var_value = int(var_value)
            elif var_type == 'dict':
                var_value = dict(var_value)
            elif var_type == 'list':
                var_value = var_value.split(';')
            var_dict[var_name] = var_value
        return var_dict
    except:
        return var_dict




#获取建设变量
def get_var(var_name):
    var_dict = gol.get_value('var_dict')
    #global var_dict
    var_vaule = var_dict.get(var_name)
    return  var_vaule

#获取ip地址
def get_address(role_name,device_id,port,index=0):
    address_mask_dict = gol.get_value('address_mask_dict')
    #global address_mask_dict
    try:
        address = address_mask_dict.get(str(role_name)+'-'+str(device_id)+port)[index].split('/')[0]
    except:
        address = ''
    return address

#获取ip掩码
def get_mask(role_name,device_id,port,index=0,type=0):
    address_mask_dict = gol.get_value('address_mask_dict')
    #global address_mask_dict
    try:
        mask = address_mask_dict.get(str(role_name)+'-'+str(device_id)+port)[index].split('/')[1]
        b = (int(mask) * "1") + ((32 - int(mask)) * "0")
        b = [int(x, 2) for x in (b[:8],b[8:16],b[16:24],b[24:])]
        maskb = "%s.%s.%s.%s" % tuple(b)
        if type == 0:
            mask = maskb
    except:
        mask = ''
    return mask

#获取地址网关
def get_gateway(role_name,device_id,port,index=0):
    address_mask_dict = gol.get_value('address_mask_dict')
    #global address_mask_dict
    try:
        address_mask = address_mask_dict.get(str(role_name)+'-'+str(device_id)+port)[index]
        net = ipaddress.ip_network(address_mask, strict=False)
        gateway = str([x for x in net.hosts()][0])
    except:
        gateway = ''
    return gateway



#根据设备类型和id获取设备名
def get_hostname(role,device_id):
    device_name_dict = gol.get_value('device_name_dict')
    #global device_name_dict
    device_name = device_name_dict.get(role+'-'+str(device_id))
    return device_name


#根据设备和接口获取端口描述
def get_port_description(role,id,port):
    link_table = gol.get_value('link_table')
    device_name_dict = gol.get_value('device_name_dict')
    #global link_table
    port_desc = ''
    for i in link_table:
        if i[0].split('-')[-2]+i[0].split('-')[-1] == role+str(id) and i[2].split('-')[-2]+i[2].split('-')[-1] == port:
            port_desc = 'To-'+device_name_dict.get(i[2])+'-'+i[3]
            break
    return port_desc



def build_config(project_name,device_list):
    template_path = '%s/templates'%(os.getcwd())
    loader = FileSystemLoader(template_path)
    env = Environment(loader=loader)
    for device in device_list:
        device_id = int(device.split('-')[-1])
        role = device.split('-')[-2]
        template = env.get_template('%s.cfg'%role)
        file = template.render(
            get_port_description=get_port_description,
            get_hostname=get_hostname,
            device_id=device_id,
            get_var=get_var,
            convert_mask=convert_mask,
            get_gateway=get_gateway,
            get_address=get_address,
            get_mask=get_mask,
            str=str
        )
        with open('%s/config/%s.cfg'%(project_name,get_hostname(role,device_id)),'w') as f:
            f.write(file)
    return 'success'






