import pandas as pd
from pyvis.network import Network
from pathlib import Path
import json

def visualize_graph_from_parquet(project_root_dir: Path, output_html_file: str = "knowledge_graph_visualization.html"):
    """
    从 GraphRAG 生成的 entities.parquet 和 relationships.parquet 文件中读取数据，
    并使用 Pyvis 进行可视化。此次修改旨在通过实体 'title' 来匹配关系。

    Args:
        project_root_dir (Path): GraphRAG 项目的根目录，
                                 其中包含 'output' 文件夹和 Parquet 文件。
        output_html_file (str): 生成的 HTML 文件的名称。
    """
    entities_path = project_root_dir / "output" / "entities.parquet"
    relationships_path = project_root_dir / "output" / "relationships.parquet"
    print(entities_path)
    if not entities_path.exists():
        print(f"Error: entities.parquet not found at {entities_path}")
        return
    if not relationships_path.exists():
        print(f"Error: relationships.parquet not found at {relationships_path}")
        return

    print(f"Reading entities from {entities_path}")
    entities_df = pd.read_parquet(entities_path)
    print(f"Reading relationships from {relationships_path}")
    relationships_df = pd.read_parquet(relationships_path)

    print(f"Loaded {len(entities_df)} entities and {len(relationships_df)} relationships.")
    print(f"Entities DataFrame columns: {entities_df.columns.tolist()}")
    print(f"Relationships DataFrame columns: {relationships_df.columns.tolist()}")

    # --- Debugging Data Types and IDs/Titles ---
    print("\n--- Debugging Data Types and IDs/Titles ---")
    if 'id' in entities_df.columns:
        print(f"Entities 'id' column dtype: {entities_df['id'].dtype}")
        print(f"Sample Entities 'id' values: {entities_df['id'].head().tolist()}")
        print(f"Number of unique entity IDs: {entities_df['id'].nunique()}")
    if 'title' in entities_df.columns:
        print(f"Entities 'title' column dtype: {entities_df['title'].dtype}")
        print(f"Sample Entities 'title' values: {entities_df['title'].head().tolist()}")
        print(f"Number of unique entity titles: {entities_df['title'].nunique()}")
        print(f"Total entities: {len(entities_df)}")
        if entities_df['title'].nunique() != len(entities_df):
            print("Warning: Entities 'title' column contains duplicates! If used for matching, this can cause issues.")

    if 'source' in relationships_df.columns and 'target' in relationships_df.columns:
        print(f"Relationships 'source' column dtype: {relationships_df['source'].dtype}")
        print(f"Relationships 'target' column dtype: {relationships_df['target'].dtype}")
        print(f"Sample Relationships 'source' values: {relationships_df['source'].head().tolist()}")
        print(f"Sample Relationships 'target' values: {relationships_df['target'].head().tolist()}")
    print("------------------------------------\n")
    # --- Debugging Data Types and IDs/Titles End ---

    # 创建一个 Network 对象
    net = Network(notebook=True, height="750px", width="100%", bgcolor="#222222", font_color="white", directed=True) # type: ignore
    net.barnes_hut()

    # 1. 添加节点
    if 'id' not in entities_df.columns or 'title' not in entities_df.columns:
        print("Error: 'id' or 'title' column missing in entities.parquet. Cannot visualize nodes.")
        return

    # **核心修改：创建从 entity_title 到 entity_id 的映射**
    # 警告：如果 title 不唯一，这里的映射只会保留最后出现的 id。
    # 比如：{"张三": "id_1", "张三": "id_2"} 最后会变成 {"张三": "id_2"}
    entity_title_to_id_map = {row['title']: row['id'] for _, row in entities_df.iterrows()}
    # 另一个方向的映射，用于根据ID获取title（如果需要）
    entity_id_to_title_map = {row['id']: row['title'] for _, row in entities_df.iterrows()}


    # 为节点添加颜色映射
    type_colors = {
        "ORGANIZATION": "lightgreen",
        "PERSON": "orange",
        "LOCATION": "lightblue",
        "EVENT": "lightcoral",
        "UNKNOWN": "gray"
    }
    default_color = "gray"

    for _, row in entities_df.iterrows():
        node_id = row['id']
        node_label = row['title'] # 节点上显示的文本是 title
        node_type = row.get('type', 'UNKNOWN')
        node_description = row.get('description', ['No description available.'])
        if isinstance(node_description, list):
            node_description = "\n".join(node_description)

        node_degree = row.get('degree', 1)

        color = type_colors.get(node_type, default_color)

        tooltip_html = f"<b>Title:</b> {node_label}<br>" \
                       f"<b>Type:</b> {node_type}<br>" \
                       f"<b>Description:</b> {node_description}<br>" \
                       f"<b>Degree:</b> {node_degree}"

        net.add_node(
            node_id, # Pyvis 内部依然使用唯一 ID 作为节点标识
            label=node_label,
            color=color,
            title=tooltip_html,
            value=node_degree * 0.5 + 5,
        )

    # 2. 添加边
    if 'source' not in relationships_df.columns or 'target' not in relationships_df.columns:
        print("Error: 'source' or 'target' column missing in relationships.parquet. Cannot visualize edges.")
        return

    relationships_added_count = 0
    for _, row in relationships_df.iterrows():
        # *** 关键修改：从关系DataFrame中读取的是 title ***
        source_title_from_rel = str(row['source']) # 确保是字符串
        target_title_from_rel = str(row['target']) # 确保是字符串
        
        relationship_description = row.get('description', ['Relates to'])
        if isinstance(relationship_description, list):
            relationship_description = "\n".join(relationship_description)

        relationship_weight = row.get('weight', 1)

        # 尝试通过 title 找到对应的 ID
        source_id = entity_title_to_id_map.get(source_title_from_rel)
        target_id = entity_title_to_id_map.get(target_title_from_rel)

        # 只有当两个 title 都能成功映射到各自的 ID 时，才添加边
        if source_id and target_id:
            edge_tooltip_html = f"<b>Relationship:</b> {relationship_description}<br>" \
                                f"<b>From:</b> {source_title_from_rel}<br>" \
                                f"<b>To:</b> {target_title_from_rel}<br>" \
                                f"<b>Weight:</b> {relationship_weight}"

            net.add_edge(
                source_id, # 使用查找到的 ID 进行连接
                target_id, # 使用查找到的 ID 进行连接
                title=edge_tooltip_html,
                value=relationship_weight * 0.2 + 1,
                label=relationship_description,
                physics=True,
                dashes=False
            )
            relationships_added_count += 1
        else:
            # 报告哪些 title 没有找到对应的 ID
            missing_part = []
            if not source_id:
                missing_part.append(f"source title '{source_title_from_rel}'")
            if not target_id:
                missing_part.append(f"target title '{target_title_from_rel}'")
            print(f"Warning: Skipping edge ('{source_title_from_rel}' -> '{target_title_from_rel}') because {' and '.join(missing_part)} was not found in entities.parquet (or title is duplicated).")

    print(f"Total relationships attempted: {len(relationships_df)}")
    print(f"Total relationships successfully added: {relationships_added_count}")


    # 3. 生成并保存 HTML 文件
    output_path = project_root_dir / output_html_file
    net.show(str(output_path))

    print(f"知识图谱已保存到 {output_path}。请在浏览器中打开此文件查看。")


# --- 如何使用 ---
if __name__ == "__main__":
    # 请将此路径替换为您的 GraphRAG 项目的根目录
    # 如果你的 `output` 文件夹直接在 `C:\Users\huijie\Desktop\graphrag\` 下，
    # 那么 `graphrag_project_path` 就是 `C:\Users\huijie\Desktop\graphrag\`。
    graphrag_project_path = Path("C:/Users/huijie/Desktop/graphrag/svtest")

    visualize_graph_from_parquet(graphrag_project_path)