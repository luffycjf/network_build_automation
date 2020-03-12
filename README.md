---
title: 网络建设自动化（硬件+配置批量生成）
date: 2020-03-12 15:38:33
tags: [network-hardware,network-automation,network-architecture,network-config]
keywords: [network-hardware,network-automation,network-architecture,network-config]
categories: Network-Automation
comments: true
---

## 系统背景
任何一个网络团队在规划完网络架构后都需要针对这套架构去生成对应的硬件（采购清单、连线关系、安装方案）+配置（所有设备的配置文件）方案。大公司往往都有一套非常完善的自动化建设系统，但其实想通过自动化脚本去实现这个过程一点不复杂，也不需要建立什么硬件、配置的模型，这里就展示一个通过excel规划网络方案，自动化生成网络方案的小系统。<br/>


## 硬件

先介绍一下硬件方案的规划和自动化计算逻辑。<br/>

### HLD
我们在构建一套网络方案的时候，首先做的就是hld(high level design),比如我们需要多少台接入设备，多少台核心设备，接入设备上需要多少个连接服务器的接口、需要多少个连接核心的接口。<br/>

这里举个例子，比如现在需要规划一个2000台左右规模的IDC网络架构，我们接入设备叫ASW，核心设备叫PSW。<br/>
考虑到可靠性，我们两台ASW做堆叠，一组ASW我们连接48台服务器，一共48组96台ASW。每个ASW四个上联口，2个堆叠口，2个备份口<br/>
对应的逻辑端口规划如下：
![asw](http://119.28.225.12:81/na1.jpg)
我们上联使用4台PSW做pod核心，下联96台ASW对应96个接口，再考虑48个（按收敛比2:1）接口上联DSW，一共需要144个接口。<br/>
对应的逻辑端口规划如下：
![psw](http://119.28.225.12:81/na2.jpg)

（数据路径：network_build_automation/architectures/v1/arch.xlsx）

这里你可能会想到，虽然ASW我定义了4个PSW逻辑接口，PSW我定义了96个ASW逻辑接口，那怎么知道这些接口之间怎么互联呢。连接关系其实就是：A设备-A接口-B设备-B接口，这里有一套算法：<br/>
以ASW-PSW为例，ASW是A设备，PSW是B设备

####1. 先获取所有A设备和A接口这部分列表<br/>

我们先遍历所有的A设备[ASW-1,ASW-2...ASW-96]，获取每个ASW设备上的PSW逻辑接口[1-PSW-1,2-PSW-1,3-PSW-1,4-PSW-1].<br/>
这里说下PSW接口的名称，第一个数（1，2，3，4）字代表分组号，同一组号连接对端同一台设备；第二个数字（1，1，1，1）代表在这个分组中的使用顺序。假如你一台ASW和一台PSW之间有两个接口互联，那对应的接口应该是[1-PSW-1,1-PSW-2,2-PSW-1,2-PSW-2,3-PSW-1,3-PSW-2,4-PSW-1,4-PSW-2]，无论你在excel中怎么填写，系统始终会按照先排序组号（1，2，3，4），后排序组内顺序号（1，2）来排序这个列表。<br/>
这样我们就生成了连接关系的左半边：<br/>
[ASW-1,1-PSW-1]<br/>
[ASW-1,2-PSW-1]<br/>
[ASW-1,3-PSW-1]<br/>
[ASW-1,4-PSW-1]<br/>
......<br/>
[ASW-96,1-PSW-1]<br/>
[ASW-96,2-PSW-1]<br/>
[ASW-96,3-PSW-1]<br/>
[ASW-96,4-PSW-1]<br/>


####2. 再获取所有B设备和B接口这部分列表<br/>
A设备是先遍历的设备列表，B设备则需要先遍历接口列表。B设备逻辑接口列表是[1-ASW-1,2-ASW-1....96-ASW-1],如我们刚刚所说这组接口代表96个端口分组，需要连接96个不同的对端设备，每个设备一个接口。因此我们遍历接口，按组号遍历，如果一个组里面有两个就遍历两次。<br/>
生成连接关系右半边：<br/>
[PSW-1,1-ASW-1]<br/>
[PSW-2,1-ASW-1]<br/>
[PSW-3,1-ASW-1]<br/>
......<br/>
[PSW-2,96-ASW-1]<br/>
[PSW-3,96-ASW-1]<br/>
[PSW-4,96-ASW-1]<br/>

最终将两个接口列表合并则生成完整的互联关系。<br/>



### LLD

####1. 规划硬件实例
有了逻辑规划实例，剩下就是根据实际需求映射对应的物理设备做LLD了。首先我们需要一个48x25G+8x100G的ASW，就拿H3C的LS-6820-56HF为例，生成一份该设备的硬件信息数据表。（数据路径：network_build_automation/architectures/v1/hardware_info.xlsx）<br/>
![asw](http://119.28.225.12:81/na3.png)<br/>
这里注意，需要填写对应端口的速率，因为端口在某些交换机上（比如华为CE盒式设备上40GE和10GE端口号上一样的）没办法通过端口号区分端口，必须加上速率或者前缀来区分。<br/>
同样的，我们需要一个144x100G的设备，这里用H3C的LS-12504X-AF配上4块LSXM1CGQ36HB1（36x100G）的板卡刚刚好，我也不知道12504是否支持这个板卡，这里只做数据演示，不代表实际使用方式。<br/>
![psw](http://119.28.225.12:81/na4.png)<br/>

####2. 端口映射
这样两台设备对应的物料硬件信息就有了，剩下就需要将逻辑端口和真实物理端口进行mapping，这里也很简单，在excel中将逻辑端口和物理端口根据实际使用规则一一对应即可（数据路径：network_build_automation/architectures/v1/port_map.xlsx）：<br/>
![psw](http://119.28.225.12:81/na5.png)<br/>
这里带上bandwidth的原因和之前一样，也是部分设备没办法直接通过端口号区分端口。<br/>


####3. 建设时生成物理连接关系和清单
有了逻辑设备的连接关系、逻辑口和物理口的映射关系，我们就可以把HLD中生成的连接关系换成物理口的连接关系。<br/>
建设的时候我们可能不是满配建设，需要填写需要购买设备数量和清单。这里需要注意，除了ASW的数量和PSW的数量，我们还需要填写对应逻辑口角色SE(服务器)、BACKUP（备份）、DSW（pod上联核心）的数量，如果不填写则代表ASW和PSW上这部分互联端口所需物料（模块+板卡）不会够买。例如在实际建设的时候一台ASW因为电力原因只能接40个服务器，并且一共只需要20台ASW，则填写信息如下表（数据路径：network_build_automation/architectures/v1/st/build.xlsx）<br/>
![order](http://119.28.225.12:81/na6.png)<br/>
并且需要给对应设备分配机架位，这是为了生成设备名需要<br/>
![order](http://119.28.225.12:81/na7.png)<br/>
这样我们就可以知道设备需要建多少台，没一台设备上的端口连接有哪些了。根据连接的端口我们查询LLD做的硬件规划信息，就可以知道对应端口的模块和板卡信息，以此计算出所需的物料信息。（除了模块和板卡，其他物料都是按照LLD中硬件规划全量购买）




## 配置

有了硬件清单和连接关系，剩下就是设备配置的生成了。
我们都知道配置其实就是模版写好后替换参数，这里我们可以用python的jinja2模块，使用jinja模版来编写配置模版。

例如ASW的配置如下：（这里我只做功能演示，以防涉及敏感数据，所以删了很多配置。数据路径：network_build_automation/architectures/v1/templates/asw.cfg）

```javascript
{% if device_id%2 == 1 %}
#
system-view
#
 sysname {{ device_name }}
#
 clock timezone BeiJing add 08:00:00
#
 super password role network-admin simple {{get_var('admin_pass')}}
#
 undo ip http enable
#
ip vpn-instance mgt
#
 dhcp enable
 irf domain {{ (get_var('pod_num')*1000+(device_id+1)/2) | int }}
 irf member 1 priority 10
 irf member 2 priority 1
 irf member 1 description {{ get_hostname('asw',device_id) }}
 irf member 2 description {{ get_hostname('asw',device_id+1) }}
#
irf-port 1/1
 port group interface HundredGigE1/0/29
 port group interface HundredGigE1/0/30
#
irf-port 2/2
 port group interface HundredGigE2/0/29
 port group interface HundredGigE2/0/30
#
 fan prefer-direction slot 1 port-to-power
 fan prefer-direction slot 2 port-to-power
#
 lldp ignore-pvid-inconsistency
#
 system-working-mode standard
#
 password-recovery enable
#
 scheduler logfile size 16
#
acl basic 2020
 description mgt-filter
 {% for mgt_subnet in get_var('mgt_subnets') %}
 rule permit vpn-instance mgt source {{ mgt_subnet.split('/')[0] }} {{ convert_mask(mgt_subnet.split('/')[1]) }}
 {% endfor %}
 {% for snmp_subnet in get_var('snmp_subnets') %}
 rule permit vpn-instance mgt source {{ snmp_subnet.split('/')[0] }} {{ convert_mask(snmp_subnet.split('/')[1]) }}
 {% endfor %}
#
domain system
 state block
#
domain jeffry_domain
 authentication login hwtacacs-scheme jeffry_scheme local
 authorization login hwtacacs-scheme jeffry_scheme local
 accounting login hwtacacs-scheme jeffry_scheme local
 authorization command hwtacacs-scheme jeffry_scheme none
 accounting command hwtacacs-scheme jeffry_scheme
#
domain default enable jeffry_domain
#
 role default-role enable
#
local-user {{ get_var('user') }} class manage
 password simple {{ get_var('pass') }}
 service-type terminal ssh
 authorization-attribute user-role network-admin
 undo authorization-attribute user-role network-operator
#
public-key local create rsa
1024
public-key local create dsa
1024
#
ssh server enable
ssh user {{ get_var('user') }} service-type all authentication-type password
#
 stp bpdu-protection
 stp global enable
 stp region-configuration
 region-name stp_a
 revision-level 1
 active region-configuration
#
vlan 100
 description Server-Access
#
interface Loopback0
 ip address {{ get_address('ASW',device_id,'loopback0') }} {{ get_mask('ASW',device_id,'loopback0') }}
#
interface Vlan-interface100
 description Server-Access
 ip address {{ get_address('ASW',device_id,'vlan100') }} {{ get_mask('ASW',device_id,'vlan100') }}
 dhcp select relay
 {% for dhcp_add in get_var('dhcp_adds') %}
 dhcp relay server-address {{ dhcp_add }}
 {% endfor %}
#
interface M-GigabitEthernet0/0/0
 description mgt
 ip binding vpn-instance mgt
 ip address {{ get_address('ASW',device_id,'mgt') }} {{ get_mask('ASW',device_id,'mgt') }}
#
interface HundredGigE1/0/25
 port link-mode route
 description {{ get_port_description('ASW',device_id,'PSW1') }}
 ip address {{ get_address('ASW',device_id,'PSW1') }} {{ get_mask('ASW',device_id,'PSW1') }}
 lldp tlv-enable basic-tlv management-address-tlv {{ get_address('ASW',device_id,'PSW1') }}
 qos trust dscp
#
bgp {{ ((device_id+1)/2) | int }}
 non-stop-routing
 router-id {{ get_address('ASW',device_id,'PSW1') }}
 compare-different-as-med
 group PSW external
   peer PSW as-number {{ (600+get_var('pod_num')) | int }}
   peer PSW route-update-interval 5
   peer PSW password simple {{ get_var('bgp_key') }}
   peer {{ get_address('PSW','1','ASW'+str(device_id)) }}
   peer {{ get_address('PSW','1','ASW'+str(device_id)) }} group PSW
   peer {{ get_address('PSW','1','ASW'+str(device_id)) }} description {{ get_hostname('PSW',1) }}
   peer {{ get_address('PSW','1','ASW'+str(device_id)) }} group PSW
 address-family ipv4 unicast
   balance 8
   preference 10 100 100
   network {{ get_address('ASW',device_id,'vlan100') }} {{ get_mask('ASW',device_id,'vlan100') }}
   peer PSW enable
   peer PSW route-policy To-PSW export
   peer PSW route-policy From-PSW import
   peer PSW advertise-community
#
ip route-static vpn-instance mgt 0.0.0.0 0.0.0.0 M-GigabitEthernet0/0/0 {{ get_gateway('ASW',device_id,'mgt') }} preference 5 description Management
#
 info-center logbuffer size 1024
 info-center source default loghost level informational
 info-center source SHELL logbuffer deny
 info-center loghost source M-GigabitEthernet0/0/0
 {% for syslog_add in get_var('syslog_adds') %}
  info-center loghost vpn-instance mgt {{ syslog_add }} facility local1
 {% endfor %}
#
 snmp-agent community read jeffry acl 2020
 snmp-agent sys-info version v2c
 undo snmp-agent sys-info version v3
 snmp-agent packet max-size 17940
 {% for snmp_add in snmp_adds %}
 snmp-agent target-host trap address udp-domain {{ snmp_add }} vpn-instance mgt params securityname jeffry v2c
 {% endfor %}
#
 ntp-service enable
 ntp-service source M-GigabitEthernet0/0/0
 ntp-service unicast-server {{ get_var('ntp_add') }} vpn-instance mgt
#
 ssh server acl 2020
#
user-interface aux 0 1
 user-role network-admin
 authentication-mode scheme
 command accounting
user-interface vty 0 63
 user-role network-admin
 user-role network-operator
 authentication-mode scheme
 command authorization
 command accounting
#
return
#
save force
#
{% else %}
#
{% endif %}
```

模版这里严格遵许[jinja2的语法](https://www.jianshu.com/p/f04dae701361)，我编写了几个获取参数的函数，列入get_var就是获取var.excel（数据路径：network_build_automation/architectures/v1/st/var.xlsx）里面参数的，这个参数表记录了和建设配置相关的一些变量信息。还有比如get_hostname、get_port_description是根据前面的硬件信息获取来的。<br/>

最后说一下ip地址规划，我写了一个函数get_address从excel（数据路径：network_build_automation/architectures/v1/st/address.xlsx）中获取。<br/>
我们这个架构需要的地址分为：ASW-PSW的互联地址、服务器业务地址、设备loopback和管理地址。<br/>

* 互联地址：我们96台ASW，每台ASW四个上联，就是96x4x2个互联地址，就是3个C的地址段
* 业务地址：48组，每组下面40个服务器（/26），48x（1/4个C），也就是12个C的地址段
* loopback地址:100台设备，1/2个C就够用
* 管理地址：100台设备，1/2个C
<br/>
这样一共业务段16C可以搞定，申请/20的网段就够用，管理地址用/25的网段就行。接下来通过excel的CONCATENATE函数将对应网段拼接成每个接口地址就可以了。每次建设只需要在第一个sheet表下填写对应的网段信息就可以生成所有接口的ip地址，函数get_address会根据设备名和接口信息获取对应的地址。
![address](http://119.28.225.12:81/na8.png)<br/>
![address](http://119.28.225.12:81/na9.png)<br/>


#总结
系统目录下执行python build.py，输入架构版本和项目名称，及可运行。测试用例版本叫v1，项目名称叫st。<br/>

项目整体结构是：

* network_build_automation/ python程序代码，如果需要添加配置模版函数修改build_config.py即可
* network_build_automation/architectures/ 架构版本目录
* network_build_automation/architectures/v1 测试v1版本目录，里面存放关于这个架构的架构HLD规划信息（arch.xlsx）、地址裂解模版（address_template.xlsx）、LLD硬件规划信息（hardware_info.xlsx）、端口映射信息（port_map.xlsx）
* network_build_automation/architectures/v1/st 测试项目st目录，里面存放着建设需求信息（build.xlsx）、建设参数表（build.xlsx）和这次项目的ip裂解表（address.xlsx）
* network_build_automation/architectures/v1/st/config 配置生成目录

必要模块安装：
pip install prettytable jinja2 xlrd xlwt ipaddress
github地址：
[https://github.com/luffycjf/network_build_automation](https://github.com/luffycjf/network_build_automation)









