# -*- coding: utf-8 -*-
# author:jeffrycheng
# project:network_build_automation
# date:2020-03-11


from build_config import *
from build_hardware import *
import os,gol

def main():
    gol._init()
    arch_version = raw_input('please input the arch version:\n')
    project_name = raw_input('please input the project name:\n')
    os.chdir('architectures/%s'%arch_version)
    gol.set_value('var_dict',load_var(project_name))
    gol.set_value('address_mask_dict',load_address_mask(project_name))
    #var_dict = load_var(project_name)
    #address_mask_dict = load_address_mask(project_name)
    device_roles,device_list,last_link_table,device_name_dict = build_hardware(project_name)
    gol.set_value('device_roles',device_roles)
    gol.set_value('device_list',device_list)
    gol.set_value('link_table',last_link_table)
    gol.set_value('device_name_dict',device_name_dict)
    result = build_config(project_name,device_list)

if __name__ == '__main__':
    main()