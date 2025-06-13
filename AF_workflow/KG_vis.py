import pandas as pd
from pyvis.network import Network
import json
import os

def visualize_graph(root_dir,type):
    """
    从 GraphRAG 生成的 entities.parquet 和 relationships.parquet 文件中读取数据，
    并使用 Pyvis 进行可视化。此版本专注于只保留知识图谱显示功能，去除所有Pyvis生成的菜单和页面元素。

    Args:
        project_root_dir (Path): GraphRAG 项目的根目录，
                                 其中包含 'output' 文件夹和 Parquet 文件。
        output_html_file (str): 生成的 HTML 文件的名称。
    """

    mid_dir=None
    if type == 'rtl':
        mid_dir="rtl_parquet"
    elif type == 'spec':
        mid_dir="output"

    entities_path=os.path.join(root_dir,f"{mid_dir}/entities.parquet")
    relationships_path=os.path.join(root_dir,f"{mid_dir}/relationships.parquet")

    print(f"📁 检查文件路径: {entities_path}")
    if os.path.exists(entities_path) is False:
        print(f"❌ Error: entities.parquet not found at {entities_path}")
        return
    if os.path.exists(relationships_path) is False:
        print(f"❌ Error: relationships.parquet not found at {relationships_path}")
        return

    print(f"📊 Reading entities from {entities_path}")
    entities_df = pd.read_parquet(entities_path)
    print(f"🔗 Reading relationships from {relationships_path}")
    relationships_df = pd.read_parquet(relationships_path)

    print(f"✅ Loaded {len(entities_df)} entities and {len(relationships_df)} relationships.")
    print(f"📋 Entities columns: {entities_df.columns.tolist()}")
    print(f"📋 Relationships columns: {relationships_df.columns.tolist()}")

    # 创建增强的网络对象
    # 关键修改：select_menu=False, filter_menu=False
    net = Network(
        notebook=True, 
        height="100%",  # 设置高度为100%以填充整个页面
        width="100%",   # 设置宽度为100%以填充整个页面
        bgcolor="#1e1e2e",  # 深色背景
        # font_color="#cdd6f4",  # 柔和的白色字体
        font_color=False,
        directed=True,
        select_menu=False,  # 禁用选择菜单
        filter_menu=False,  # 禁用过滤菜单
        # cdn_resources='in_line' # 如果在Jupyter Notebook中遇到图形显示问题，请取消此行的注释
    )
    
    # 设置物理引擎参数，使布局更美观
    net.set_options(json.dumps({
        "physics": {
            "enabled": True,
            "barnesHut": {
                "gravitationalConstant": -2000,
                "centralGravity": 0.1,
                "springLength": 200,
                "springConstant": 0.05,
                "damping": 0.9,
                "avoidOverlap": 0.5
            },
            "maxVelocity": 50,
            "minVelocity": 0.1,
            "timestep": 0.35,
            "stabilization": {"iterations": 150}
        },
        "nodes": {
            "borderWidth": 2,
            "borderWidthSelected": 4,
            "shadow": {
                "enabled": True,
                "color": "rgba(0,0,0,0.3)",
                "size": 10,
                "x": 2,
                "y": 2
            },
            "font": {
                "size": 14,
                "face": "arial",
                "color": "#ffffff"
            },
            "title": {    # 启用节点的HTML标题渲染
                "enabled": True,
                "allowHTML": True 
            }
        },
        "edges": {
            "smooth": {
                "enabled": True,
                "type": "dynamic",
                "roundness": 0.2
            },
            "arrows": {
                "to": {
                    "enabled": True,
                    "scaleFactor": 0.8
                }
            },
            "shadow": {
                "enabled": True,
                "color": "rgba(0,0,0,0.2)",
                "size": 5,
                "x": 1,
                "y": 1
            },
            "font": {
                "size": 12,
                "color": "#ffffff",
                "strokeWidth": 2,
                "strokeColor": "#1e1e2e",
                "background": "none"
            },
            "title": {    # 启用边的HTML标题渲染
                "enabled": True,
                "allowHTML": True
            }
        },
        "interaction": {
            "hover": True,
            "hoverConnectedEdges": True,
            "selectConnectedEdges": True,
            "zoomView": True,
            "dragView": True
        },
        "layout": {
            "improvedLayout": True
        }
    }))

    # 检查必要列
    if 'id' not in entities_df.columns or 'title' not in entities_df.columns:
        print("❌ Error: 'id' or 'title' column missing in entities.parquet")
        return

    # 创建映射
    entity_title_to_id_map = {row['title']: row['id'] for _, row in entities_df.iterrows()}
    entity_id_to_title_map = {row['id']: row['title'] for _, row in entities_df.iterrows()}


    default_color = "#6c7086"
    default_shape = "dot"

    print("🎨 Adding nodes with enhanced styling...")
    
    # 添加节点
    for _, row in entities_df.iterrows():
        node_id = row['id']
        node_label = row['title']
        node_type = row.get('type', 'UNKNOWN')
        node_description = row.get('description', ['No description available.'])
        
        if isinstance(node_description, list):
            node_description = "\n".join(node_description)
        
        # 限制描述长度，避免工具提示过长
        if len(node_description) > 200:
            node_description = node_description[:200] + "..."

        node_degree = row.get('degree', 1)
        
        color = default_color
        shape = default_shape
        
        # 根据度数调整节点大小
        node_size = max(10, min(50, node_degree * 2 + 15))

        # 创建更丰富的工具提示 HTML
        tooltip_html = f"""
            Title:{node_label}
            Type: {node_type}
            Connections: {node_degree}
            Description: {node_description}
        """

        net.add_node(
            node_id,
            label=node_label,
            color=color,
            title=tooltip_html, # 将HTML字符串作为title传入
            value=node_size,
            shape=shape,
            borderWidth=2,
            borderWidthSelected=4
        )

    print(f"✅ Added {len(entities_df)} nodes")

    # 添加边
    if 'source' not in relationships_df.columns or 'target' not in relationships_df.columns:
        print("❌ Error: 'source' or 'target' column missing in relationships.parquet")
        return

    print("🔗 Adding relationships with enhanced styling...")
    
    relationships_added_count = 0
    skipped_relationships = []
    
    for _, row in relationships_df.iterrows():
        source_title_from_rel = str(row['source'])
        target_title_from_rel = str(row['target'])
        
        relationship_description = row.get('description', ['Relates to'])
        if isinstance(relationship_description, list):
            relationship_description = "\n".join(relationship_description)
            
        # 限制关系描述长度
        if len(relationship_description) > 100:
            relationship_description = relationship_description[:100] + "..."

        relationship_weight = row.get('weight', 1)

        source_id = entity_title_to_id_map.get(source_title_from_rel)
        target_id = entity_title_to_id_map.get(target_title_from_rel)

        if source_id and target_id:
            # 根据权重设置边的颜色和宽度
            edge_width = max(1, min(8, relationship_weight * 2))
            
            # 权重越高，边越明亮
            if relationship_weight > 0.8:
                edge_color = "#f38ba8"  # 高权重 - 亮粉色
            elif relationship_weight > 0.5:
                edge_color = "#fab387"  # 中等权重 - 橙色
            else:
                edge_color = "#6c7086"  # 低权重 - 灰色

            edge_tooltip_html = f"""
            From:{source_title_from_rel}
            To:{target_title_from_rel}
            Weight:{relationship_weight:.2f}
            Relationship: {relationship_description}
            """
            net.add_edge(
                source_id,
                target_id,
                title=edge_tooltip_html, # 将HTML字符串作为title传入
                width=edge_width,
                color=edge_color,
                physics=True,
                smooth=True
            )
            relationships_added_count += 1
        else:
            missing_parts = []
            if not source_id:
                missing_parts.append(f"source '{source_title_from_rel}'")
            if not target_id:
                missing_parts.append(f"target '{target_title_from_rel}'")
            skipped_relationships.append(f"{source_title_from_rel} -> {target_title_from_rel}")

    print(f"✅ Added {relationships_added_count} relationships")
    if skipped_relationships:
        print(f"⚠️  Skipped {len(skipped_relationships)} relationships due to missing entities")
        if len(skipped_relationships) <= 5:
            for rel in skipped_relationships:
                print(f"   • {rel}")
        else:
            print(f"   • First 5: {', '.join(skipped_relationships[:5])}")
            print(f"   • ... and {len(skipped_relationships) - 5} more")

    # 生成输出文件
    output_path = os.path.join(root_dir,f"{type}_graph.html")
    
    # 直接调用 net.show() 生成 HTML
    net.show(str(output_path))
    
    # 进一步修改生成的HTML文件，以确保没有额外的边距和滚动条，并全屏显示
    with open(output_path, 'r', encoding='utf-8') as f:
        html_content = f.read()

    # 替换<body>标签，使其充满整个视口，并设置背景色
    # 找到<body>标签，并替换其样式
    modified_html_content = html_content.replace(
        '<body>',
        f'<body style="margin: 0; padding: 0; overflow: hidden; background-color: {net.bgcolor};">'
    )
    
    # 找到 #mynetworkid 的样式，确保它也充满整个视口
    # 假设 Pyvis 会生成 <div id="mynetworkid"></div> 并且其样式在 <head> 标签中
    # 我们需要确保其 style 属性是 full width/height
    # 这部分可能需要更复杂的正则匹配，但通常Pyvis会将其放在head的style标签中
    # 为了鲁棒性，我们也可以直接在body中嵌入style标签来覆盖它。
    # 这里我们尝试替换现有的样式，如果失败，可以考虑注入新的style标签
    
    # 尝试查找并替换 #mynetworkid 的样式
    # 这是Pyvis生成的默认id和其可能有的样式
    # 查找 <div id="mynetworkid" style="width: 800px; height: 500px;">
    # 替换成 <div id="mynetworkid" style="width: 100vw; height: 100vh;">
    modified_html_content = modified_html_content.replace(
        '<div id="mynetwork" style="width: 800px; height: 500px;">', # Pyvis默认生成的div id是mynetwork
        '<div id="mynetwork" style="width: 100vw; height: 100vh;">'
    )
    
    # 为了更彻底，确保body和html元素没有默认的margin和padding
    # 可以在 <head> 中注入新的 <style> 标签来覆盖所有可能存在的默认样式
    head_end_tag = modified_html_content.find('</head>')
    if head_end_tag != -1:
        custom_css = """
        <style type="text/css">
            html, body {
                margin: 0;
                padding: 0;
                overflow: hidden;
                width: 100%;
                height: 100%;
            }
            #mynetwork {
                width: 100vw;
                height: 100vh;
                margin: 0;
                padding: 0;
            }
        </style>
        """
        modified_html_content = modified_html_content[:head_end_tag] + custom_css + modified_html_content[head_end_tag:]

    # 再次写入文件
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(modified_html_content)

    print("\n" + "="*60)
    print("🎉 可视化完成！")
    print("="*60)
    print(f"📄 输出文件: {output_path}")
    print(f"📊 图谱统计:")
    print(f"   • 总实体数: {len(entities_df)}")
    print(f"   • 已添加关系数: {relationships_added_count}")
    print("="*60)
    print("🌐 请在浏览器中打开HTML文件查看图谱可视化！")
    print("💡 建议使用 Chrome, Firefox 或 Edge 浏览器以获得最佳体验。")


# 使用示例
# if __name__ == "__main__":
#     # 请将此路径替换为您的 GraphRAG 项目的根目录
#     graphrag_project_path = Path("C:/Users/huijie/Desktop/graphrag/svtest2")
    
#     print("🚀 启动知识图谱可视化...")
#     print("="*60)
    
#     visualize_graph_from_parquet(graphrag_project_path)


# import pandas as pd # 虽然不再直接读取parquet，但pd可能仍用于一些数据处理或查看，这里保留
# from pyvis.network import Network
# from pathlib import Path
# import json
# import random # 这个库在这里似乎没有被用到，可以按需移除

# def visualize_graph_from_data(entities_data: list, relationships_data: list, output_html_file: str = "knowledge_graph_visualization.html"):
#     """
#     直接从提供的实体和关系列表（Python 字典格式）构建知识图谱，
#     并使用 Pyvis 进行可视化。此版本专注于只保留知识图谱显示功能，
#     去除所有 Pyvis 生成的菜单和页面元素。

#     Args:
#         entities_data (list): 包含实体信息的字典列表。
#         relationships_data (list): 包含关系信息的字典列表。
#         output_html_file (str): 生成的 HTML 文件的名称。
#     """
    
#     print(f"✅ Loaded {len(entities_data)} entities and {len(relationships_data)} relationships from provided data.")
    
#     # 关键修改：直接使用传入的列表数据，不再从parquet读取
#     # 为了方便后续处理，我们可以将其转换为DataFrame（如果数据量不大），
#     # 也可以直接操作列表。这里为了保持与原代码逻辑相似，我们创建临时的DataFrame。
#     entities_df = pd.DataFrame(entities_data)
#     relationships_df = pd.DataFrame(relationships_data)


#     print(f"📋 Entities columns: {entities_df.columns.tolist()}")
#     print(f"📋 Relationships columns: {relationships_df.columns.tolist()}")

#     # 创建增强的网络对象
#     # 关键修改：select_menu=False, filter_menu=False
#     net = Network(
#         notebook=True, 
#         height="100%",  # 设置高度为100%以填充整个页面
#         width="100%",   # 设置宽度为100%以填充整个页面
#         bgcolor="#1e1e2e",   # 深色背景
#         font_color=False, # Pyvis的font_color设为False时，会使用nodes配置中的font.color
#         directed=True,
#         select_menu=False,   # 禁用选择菜单
#         filter_menu=False,   # 禁用过滤菜单
#         # cdn_resources='in_line' # 如果在Jupyter Notebook中遇到图形显示问题，请取消此行的注释
#     )
    
#     # 设置物理引擎参数，使布局更美观
#     net.set_options(json.dumps({
#         "physics": {
#             "enabled": True,
#             "barnesHut": {
#                 "gravitationalConstant": -2000,
#                 "centralGravity": 0.1,
#                 "springLength": 200,
#                 "springConstant": 0.05,
#                 "damping": 0.9,
#                 "avoidOverlap": 0.5
#             },
#             "maxVelocity": 50,
#             "minVelocity": 0.1,
#             "timestep": 0.35,
#             "stabilization": {"iterations": 150}
#         },
#         "nodes": {
#             "borderWidth": 2,
#             "borderWidthSelected": 4,
#             "shadow": {
#                 "enabled": True,
#                 "color": "rgba(0,0,0,0.3)",
#                 "size": 10,
#                 "x": 2,
#                 "y": 2
#             },
#             "font": {
#                 "size": 14,
#                 "face": "arial",
#                 "color": "#ffffff" # 节点字体颜色
#             },
#             "title": {    # 启用节点的HTML标题渲染
#                 "enabled": True,
#                 "allowHTML": True 
#             }
#         },
#         "edges": {
#             "smooth": {
#                 "enabled": True,
#                 "type": "dynamic",
#                 "roundness": 0.2
#             },
#             "arrows": {
#                 "to": {
#                     "enabled": True,
#                     "scaleFactor": 0.8
#                 }
#             },
#             "shadow": {
#                 "enabled": True,
#                 "color": "rgba(0,0,0,0.2)",
#                 "size": 5,
#                 "x": 1,
#                 "y": 1
#             },
#             "font": {
#                 "size": 12,
#                 "color": "#ffffff", # 边字体颜色
#                 "strokeWidth": 2,
#                 "strokeColor": "#1e1e2e",
#                 "background": "none"
#             },
#             "title": {    # 启用边的HTML标题渲染
#                 "enabled": True,
#                 "allowHTML": True
#             }
#         },
#         "interaction": {
#             "hover": True,
#             "hoverConnectedEdges": True,
#             "selectConnectedEdges": True,
#             "zoomView": True,
#             "dragView": True
#         },
#         "layout": {
#             "improvedLayout": True
#         }
#     }))

#     # 检查必要列
#     if 'id' not in entities_df.columns or 'title' not in entities_df.columns:
#         print("❌ Error: 'id' or 'title' column missing in entities data.")
#         return

#     # 创建映射
#     entity_title_to_id_map = {row['title']: row['id'] for _, row in entities_df.iterrows()}
#     entity_id_to_title_map = {row['id']: row['title'] for _, row in entities_df.iterrows()}


#     default_color = "#6c7086"
#     default_shape = "dot"

#     print("🎨 Adding nodes with enhanced styling...")
    
#     # 添加节点
#     for _, row in entities_df.iterrows():
#         node_id = row['id']
#         node_label = row['title']
#         node_type = row.get('type', 'UNKNOWN')
#         node_description = row.get('description', 'No description available.')
        
#         # 确保 description 是字符串，如果它是列表，就拼接起来
#         if isinstance(node_description, list):
#             node_description = "\n".join(node_description)
        
#         # 限制描述长度，避免工具提示过长
#         # if len(node_description) > 200:
#         #     node_description = node_description[:200] + "..."

#         node_degree = row.get('degree', 1) # 默认度数为1，避免大小为0

#         color = default_color
#         shape = default_shape
        
#         # 根据度数调整节点大小
#         # 确保 node_degree 是数字，并且至少为1
#         node_degree_val = max(1, int(node_degree))
#         node_size = max(10, min(50, node_degree_val * 2 + 15))

#         # 创建更丰富的工具提示 HTML
#         tooltip_html = f"""
#             Title:{node_label}
#             Type:{node_type}
#             Connections:{node_degree_val}
#             Description:{node_description}
#         """

#         net.add_node(
#             node_id,
#             label=node_label,
#             color=color,
#             title=tooltip_html, # 将HTML字符串作为title传入
#             value=node_size,
#             shape=shape,
#             borderWidth=2,
#             borderWidthSelected=4
#         )

#     print(f"✅ Added {len(entities_df)} nodes")

#     # 添加边
#     if 'source' not in relationships_df.columns or 'target' not in relationships_df.columns:
#         print("❌ Error: 'source' or 'target' column missing in relationships data.")
#         return

#     print("🔗 Adding relationships with enhanced styling...")
    
#     relationships_added_count = 0
#     skipped_relationships = []
    
#     for _, row in relationships_df.iterrows():
#         source_title_from_rel = str(row['source'])
#         target_title_from_rel = str(row['target'])
        
#         relationship_description = row.get('description', 'Relates to')
#         # 确保 description 是字符串，如果它是列表，就拼接起来
#         if isinstance(relationship_description, list):
#             relationship_description = "\n".join(relationship_description)
            
#         # 限制关系描述长度
#         # if len(relationship_description) > 100:
#         #     relationship_description = relationship_description[:100] + "..."

#         relationship_weight = row.get('weight', 1) # 默认权重为1，确保有值

#         source_id = entity_title_to_id_map.get(source_title_from_rel)
#         target_id = entity_title_to_id_map.get(target_title_from_rel)

#         if source_id and target_id:
#             # 根据权重设置边的颜色和宽度
#             # 确保 relationship_weight 是数字，并且至少为0.1（避免宽度过小）
#             edge_weight_val = max(0.1, float(relationship_weight))
#             edge_width = max(1, min(8, edge_weight_val * 2))
            
#             # 权重越高，边越明亮
#             if edge_weight_val > 0.8:
#                 edge_color = "#f38ba8"  # 高权重 - 亮粉色
#             elif edge_weight_val > 0.5:
#                 edge_color = "#fab387"  # 中等权重 - 橙色
#             else:
#                 edge_color = "#6c7086"  # 低权重 - 灰色

#             edge_tooltip_html = f"""
#                 From: {source_title_from_rel}
#                 To: {target_title_from_rel}
#                 Weight: {edge_weight_val:.2f}
#                 Relationship: {relationship_description}
#             """
#             net.add_edge(
#                 source_id,
#                 target_id,
#                 title=edge_tooltip_html, # 将HTML字符串作为title传入
#                 width=edge_width,
#                 color=edge_color,
#                 physics=True,
#                 smooth=True
#             )
#             relationships_added_count += 1
#         else:
#             missing_parts = []
#             if not source_id:
#                 missing_parts.append(f"source '{source_title_from_rel}'")
#             if not target_id:
#                 missing_parts.append(f"target '{target_title_from_rel}'")
#             skipped_relationships.append(f"{source_title_from_rel} -> {target_title_from_rel} (Missing: {', '.join(missing_parts)})")

#     print(f"✅ Added {relationships_added_count} relationships")
#     if skipped_relationships:
#         print(f"⚠️  Skipped {len(skipped_relationships)} relationships due to missing entities:")
#         if len(skipped_relationships) <= 5:
#             for rel in skipped_relationships:
#                 print(f"    • {rel}")
#         else:
#             print(f"    • First 5: {'; '.join(skipped_relationships[:5])}")
#             print(f"    • ... and {len(skipped_relationships) - 5} more")

#     # 生成输出文件
#     # 注意：这里我们不再需要 project_root_dir，直接指定输出文件名或路径
#     output_path = Path(output_html_file) # 可以直接指定文件名，或者使用 Path('./output') / output_html_file

#     # 直接调用 net.show() 生成 HTML
#     net.show(str(output_path))
    
#     # 进一步修改生成的HTML文件，以确保没有额外的边距和滚动条，并全屏显示
#     with open(output_path, 'r', encoding='utf-8') as f:
#         html_content = f.read()

#     # 替换<body>标签，使其充满整个视口，并设置背景色
#     modified_html_content = html_content.replace(
#         '<body>',
#         f'<body style="margin: 0; padding: 0; overflow: hidden; background-color: {net.bgcolor};">'
#     )
    
#     # 为了更彻底，确保body和html元素没有默认的margin和padding
#     # 可以在 <head> 中注入新的 <style> 标签来覆盖所有可能存在的默认样式
#     head_end_tag = modified_html_content.find('</head>')
#     if head_end_tag != -1:
#         custom_css = """
#         <style type="text/css">
#             html, body {
#                 margin: 0;
#                 padding: 0;
#                 overflow: hidden;
#                 width: 100%;
#                 height: 100%;
#             }
#             #mynetwork {
#                 width: 100vw;
#                 height: 100vh;
#                 margin: 0;
#                 padding: 0;
#             }
#         </style>
#         """
#         modified_html_content = modified_html_content[:head_end_tag] + custom_css + modified_html_content[head_end_tag:]

#     # 再次写入文件
#     with open(output_path, 'w', encoding='utf-8') as f:
#         f.write(modified_html_content)

#     print("\n" + "="*60)
#     print("🎉 可视化完成！")
#     print("="*60)
#     print(f"📄 输出文件: {output_path}")
#     print(f"📊 图谱统计:")
#     print(f"    • 总实体数: {len(entities_data)}")
#     print(f"    • 已添加关系数: {relationships_added_count}")
#     print("="*60)
#     print("🌐 请在浏览器中打开HTML文件查看图谱可视化！")
#     print("💡 建议使用 Chrome, Firefox 或 Edge 浏览器以获得最佳体验。")


# # --- 使用示例 ---
# if __name__ == "__main__":
#     # 你提供的实体数据示例（请替换为你真实的完整数据）
#     my_entities = [
#         {
#             "id": "1d9cefd7-7a58-448d-b0fe-e6c5e1006309",
#             "human_readable_id": 0,
#             "title": "apb",
#             "type": "MODULE",
#             "description": "Verilog module apb is defined in line 2",
#             "text_unit_ids": "C:\\Users\\huijie\\Desktop\\graphrag\\svtest\\pre_rtl\\apb.v:2:2.",
#             "frequency": 1,
#             "degree": 2, # 假设 apb 与两个端口有连接，所以度数为2
#             "x": 0,
#             "y": 0
#         },
#         {
#             "id": "entity-id-PCLK", # 为 PCLK 提供一个实际的 ID
#             "human_readable_id": 1,
#             "title": "PCLK",
#             "type": "PORT",
#             "description": "APB bus clock signal.",
#             "text_unit_ids": "C:\\Users\\huijie\\Desktop\\graphrag\\svtest\\pre_rtl\\apb.v#3:3",
#             "frequency": 1,
#             "degree": 1, # PCLK 连接到 apb，所以度数为1
#             "x": 0,
#             "y": 0
#         },
#         {
#             "id": "entity-id-PRESETn", # 为 PRESETn 提供一个实际的 ID
#             "human_readable_id": 3,
#             "title": "PRESETn",
#             "type": "PORT",
#             "description": "APB bus reset signal (active low).",
#             "text_unit_ids": "C:\\Users\\huijie\\Desktop\\graphrag\\svtest\\pre_rtl\\apb.v#4:4",
#             "frequency": 1,
#             "degree": 1, # PRESETn 连接到 apb，所以度数为1
#             "x": 0,
#             "y": 0
#         }
#         # 添加更多实体...
#     ]

#     # 你提供的关系数据示例（请替换为你真实的完整数据）
#     my_relationships = [
#         {
#             "id": "aaa30a84-36dc-4447-9889-8c5751cbe75b",
#             "human_readable_id": 2,
#             "source": "apb",
#             "target": "PCLK",
#             "type": "CONTAINS_PORT",
#             "description": "apb contains port PCLK.",
#             "weight": 0.9, # 较高的权重
#             "combined_degree": 0,
#             "text_unit_ids": ["C:\\Users\\huijie\\Desktop\\graphrag\\svtest\\pre_rtl\\apb.v#3:3"]
#         },
#         {
#             "id": "bbb30a84-36dc-4447-9889-8c5751cbe75b",
#             "human_readable_id": 4,
#             "source": "apb",
#             "target": "PRESETn",
#             "type": "CONTAINS_PORT",
#             "description": "apb contains port PRESETn.",
#             "weight": 0.7, # 中等权重
#             "combined_degree": 0,
#             "text_unit_ids": ["C:\\Users\\huijie\\Desktop\\graphrag\\svtest\\pre_rtl\\apb.v#4:4"]
#         }
#         # 添加更多关系...
#     ]
    
#     print("🚀 启动知识图谱可视化...")
#     print("="*60)
    
#     visualize_graph_from_data(my_entities, my_relationships, "my_knowledge_graph.html")