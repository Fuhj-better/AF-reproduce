import asyncio
import glob
import os
import sys
from KG_specbuild import build_index,global_research
from KG_rtlbuild import KGBuilder
from KG_rtlparse import RTLCollectorVisitor
from KG_vis import visualize_graph 
from pyverilog.vparser.parser import parse

from helper import remove_comments

TEST_DIRECTORY = "svtest"

ROOT_DIRECTORY = os.path.join(os.path.dirname(os.path.abspath(__file__)),'../',TEST_DIRECTORY)

# async def run_KG_specbuild():
#     await build_index()


if __name__ == "__main__":
    '''
    这是主要流程函数
    '''
    #暂时不运行graphrag，太慢了
    # asyncio.run(run_KG_specbuild())

    # rtl_dir=os.path.join(ROOT_DIRECTORY,'rtl')
    # if os.path.exists(rtl_dir) is False:
    #     print(f"{rtl_dir} in {ROOT_DIRECTORY} does not exit.")
    #     sys.exit(-1)
    # in_file_list=glob.glob(os.path.join(rtl_dir, "*.v"))
    # pre_rtl_dir=os.path.join(ROOT_DIRECTORY,'pre_rtl')
    # os.makedirs(pre_rtl_dir,exist_ok=True)
    
    # for in_f in in_file_list:
    #     f_name=os.path.basename(in_f)
    #     out_f=os.path.join(pre_rtl_dir,f_name)
    #     remove_comments(in_f,out_f)
    
    # in_file_list=glob.glob(os.path.join(pre_rtl_dir, "*.v"))
    # 以下是调试的
    in_file_list=[
        f'{ROOT_DIRECTORY}\\pre_rtl\\apb.v',
        f'{ROOT_DIRECTORY}\\pre_rtl\\fifo.v',
        f'{ROOT_DIRECTORY}\\pre_rtl\\i2c.v',
        f'{ROOT_DIRECTORY}\\pre_rtl\\module_i2c.v',
    ]
    # in_file_list=[
    #     'C:\\Users\\huijie\\Desktop\\graphrag\\svtest\\pre_rtl\\i2c.v',
    # ]
    vistor= RTLCollectorVisitor()
    for f in in_file_list:
        ast,_=parse([str(f)])
        vistor.set_filepath(f)
        vistor.visit(ast)
    rtl_info=vistor.get_rtlinfo()
    static_dir=os.path.join(ROOT_DIRECTORY,'static')
    os.makedirs(static_dir,exist_ok=True)
    with open(f'{static_dir}/rtl_data.json','w',encoding='utf-8') as f:
         f.write(rtl_info.parse_node())
    
    kg=KGBuilder(rtl_info)
    entities,relationships=kg.get_kg(ROOT_DIRECTORY)
    kg_dir=os.path.join(ROOT_DIRECTORY,'kg')
    os.makedirs(kg_dir,exist_ok=True)
    with open(f'{kg_dir}/entities.json','w',encoding='utf-8') as f:
        f.write(entities)
    with open(f'{kg_dir}/relationships.json','w',encoding='utf-8') as f:
        f.write(relationships)
    visualize_graph(ROOT_DIRECTORY,"rtl")