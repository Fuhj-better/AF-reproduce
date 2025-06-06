import pandas as pd
from pyvis.network import Network
from pathlib import Path
import json
import random

def visualize_graph_from_parquet(project_root_dir: Path, output_html_file: str = "knowledge_graph_visualization.html"):
    """
    从 GraphRAG 生成的 entities.parquet 和 relationships.parquet 文件中读取数据，
    并使用 Pyvis 进行可视化。此版本专注于只保留知识图谱显示功能，去除所有Pyvis生成的菜单和页面元素。

    Args:
        project_root_dir (Path): GraphRAG 项目的根目录，
                                 其中包含 'output' 文件夹和 Parquet 文件。
        output_html_file (str): 生成的 HTML 文件的名称。
    """
    entities_path = project_root_dir / "output" / "entities.parquet"
    relationships_path = project_root_dir / "output" / "relationships.parquet"
    
    print(f"📁 检查文件路径: {entities_path}")
    if not entities_path.exists():
        print(f"❌ Error: entities.parquet not found at {entities_path}")
        return
    if not relationships_path.exists():
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
    output_path = project_root_dir / output_html_file
    
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
if __name__ == "__main__":
    # 请将此路径替换为您的 GraphRAG 项目的根目录
    graphrag_project_path = Path("C:/Users/huijie/Desktop/graphrag/svtest")
    
    print("🚀 启动知识图谱可视化...")
    print("="*60)
    
    visualize_graph_from_parquet(graphrag_project_path)