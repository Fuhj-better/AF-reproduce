
import matplotlib.pyplot as plt
import json
import uuid


class KGBuilder:
    def __init__(self,rtl_info):
        self.entities=[]
        self.relationships = []
        self.next_id=0
        self.rtl_info=rtl_info
        # 全局映射：用于存储信号名称到其对应实体的映射
        # 键可以是 (module_name, signal_name) 以处理不同模块的同名信号
        self.signal_name_to_entity_map = {} 
        # 用于 always block 内部去重控制流条件，避免为相同条件创建多个实体
        self.condition_entity_map = {} 

    def _get_human_readable_id(self):
        ret=self.next_id
        self.next_id+=1
        return ret
    
    def _get_text_unit_ids(self,type_parsed_data):
        return f"{type_parsed_data['startline']}:{type_parsed_data['endline']}"
    
    # --- 辅助方法：管理信号名称到实体标题的映射 ---
    # 这些方法是实现左右值链接到现有信号实体的关键。
    # 它们需要在你的 _build_port, _build_wire, _build_register 方法中被调用
    # 来填充 self._signal_name_to_title_map。
    
    def _add_signal_to_map(self, parent_module_name, signal_name, signal_entity):
        key = (parent_module_name, signal_name)
        self.signal_name_to_entity_map[key] = signal_entity

    def _get_signal_entity(self, parent_module_name, signal_name):
        key = (parent_module_name, signal_name)
        return self.signal_name_to_entity_map.get(key)

    def _get_senslist_summary(self, senlist):
        """根据敏感列表生成一个简洁的摘要字符串。"""
        if not senlist:
            return "None"
        parts = []
        for item in senlist:
            edge = item.get('edge', '')
            sig = item.get('sig', '')
            if edge and sig:
                parts.append(f"{edge} {sig}")
            elif sig:
                parts.append(sig)
        return ", ".join(parts)
    
    def _build_module(self,filepath,module):
        module_entity={
            "id":str(uuid.uuid4()),
            "human_readable_id":self._get_human_readable_id(),
            "title":module["name"],
            "type":"MODULE",
            "description":f"Verilog module {module['name']} is defined in line {module['lineno']}",
            "text_unit_ids":f"{filepath}:{self._get_text_unit_ids(module)}.",
            "frequency":1,
            "degree":0,
            "x":0,
            "y":0,
        }
        self.entities.append(module_entity)

    def _build_port(self,filepath,port):
      # 使用 .get() 方法安全地访问字典键，提供默认值以避免 KeyError
        port_direction = port.get('direction', 'unknown')
        port_msb = port.get('msb', 'N/A')
        port_lsb = port.get('lsb', 'N/A')
        port_dimensions = port.get('dimensions', 'N/A')
        port_ast = port.get('ast', 'N/A')
        parent_module_name=port.get('parent_module','unknown')

        description_parts = [
            f"Verilog port '{port['name']}' is defined within module '{port['parent_module']}' in file '{filepath}' ",
            f"from line {port['startline']} to line {port['endline']}.",
            f"Its direction is '{port_direction}'.",
        ]
        
        if port_msb is not None and port_lsb is not None and port_msb != 'N/A' and port_lsb != 'N/A':
            if port_msb == port_lsb:
                description_parts.append(f"It is a 1-bit signal.")
            else:
                description_parts.append(f"Its bit-width is from MSB {port_msb} to LSB {port_lsb}.")
        
        if port_dimensions and port_dimensions != 'N/A':
            description_parts.append(f"It has dimensions: {port_dimensions}.")
        
        if port_ast != 'N/A':
             description_parts.append(f"Its AST node type is '{port_ast}'.")

        # 构建端口实体字典
        port_entity = {
            "id": str(uuid.uuid4()),
            "human_readable_id": self._get_human_readable_id(),
            "title": port["name"],
            "type": "PORT",
            "description": " ".join(description_parts), # 将所有描述部分连接成一个字符串
            "text_unit_ids": [f"{filepath}#{self._get_text_unit_ids(port)}"],
            "frequency": 1,
            "degree": 0,
            "x": 0,
            "y": 0,
        }
        self.entities.append(port_entity) # 将端口实体添加到实体列表

        # --- 在这里添加关系 ---
        # 建立 Module CONTAINS Port 的关系
        # --- 按照你要求的格式添加关系 ---
        module_contain_port={
            "id": str(uuid.uuid4()), # 关系的唯一 ID
            "human_readable_id": self._get_human_readable_id(), # 关系的易读 ID
            "source": parent_module_name,     # 父模块的名称
            "target": port_entity["title"],   # 当前端口的名称
            "type": "CONTAINS_PORT",          # 关系类型
            "description": f"{parent_module_name} contains port {port_entity['title']}.", # 关系的描述
            "weight": 1, # 可以自定义权重，这里给个默认值
            "combined_degree": 0, # 如果需要，可以在构建完图谱后计算
            "text_unit_ids": [f"{filepath}#{self._get_text_unit_ids(port)}"], # 关系可能与端口代码位置关联
        }
        self.relationships.append(module_contain_port)

        self._add_signal_to_map(parent_module_name,port["name"],port_entity)
    
    def _build_wire(self, filepath, wire):
        """
        构建 Verilog 线网 (wire) 实体，并添加与父模块的包含关系。

        Args:
            filepath (str): Verilog 文件路径。
            wire (dict): 包含线网信息的字典。
            parent_module_name (str): 父模块的名称（字符串）。
        """
        # 使用 .get() 方法安全地访问字典键，提供默认值以避免 KeyError
        wire_name = wire["name"]
        wire_msb = wire.get('msb', 'N/A')
        wire_lsb = wire.get('lsb', 'N/A')
        wire_signed = wire.get('signed', False) # 默认不是有符号的
        wire_dimensions = wire.get('dimensions', 'N/A')
        wire_value = wire.get('value', None) # 默认值为 None，表示可能没有初始值
        wire_ast = wire.get('ast', 'N/A')
        wire_startline = wire.get('startline', wire.get('lineno', -1))
        wire_endline = wire.get('endline', wire.get('lineno', -1))
        parent_module_name=wire.get('parent_module_name','unknown')

        # --- 构建详细的 description 字符串 ---
        description_parts = [
            f"Verilog **wire** '{wire_name}' is defined within module '{wire['parent_module']}' ",
            f"in file '{filepath}' from line {wire_startline} to line {wire_endline}."
        ]

        # 添加位宽信息
        if wire_msb is not None and wire_lsb is not None and wire_msb != 'N/A' and wire_lsb != 'N/A':
            if wire_msb == wire_lsb:
                description_parts.append(f"It is a **1-bit** signal.")
            else:
                description_parts.append(f"Its **bit-width** is from MSB {wire_msb} to LSB {wire_lsb}.")
        
        # 添加有无符号信息
        if wire_signed:
            description_parts.append(f"It is a **signed** wire.")
        else:
            description_parts.append(f"It is an **unsigned** wire.")

        # 添加维度信息（如果存在）
        if wire_dimensions and wire_dimensions != 'N/A':
            description_parts.append(f"It has **dimensions**: {wire_dimensions}.")
        
        # 添加初始值信息（如果存在）
        if wire_value is not None and wire_value != 'None': # 明确检查 None 和字符串 'None'
            description_parts.append(f"It has an **initial value** of '{wire_value}'.")
        
        # 添加 AST 节点类型信息
        if wire_ast != 'N/A':
             description_parts.append(f"Its **AST node type** is '{wire_ast}'.")

        # 将所有描述部分连接成一个完整的字符串
        wire_description = " ".join(description_parts)

        # --- 构建线网实体字典 ---
        wire_entity = {
            "id": str(uuid.uuid4()),
            "human_readable_id": self._get_human_readable_id(),
            "title": wire_name,
            "type": "WIRE",
            "description": wire_description,
            "text_unit_ids": [f"{filepath}#{self._get_text_unit_ids(wire)}"], # text_unit_ids 通常是列表
            "frequency": 1,
            "degree": 0,
            "x": 0,
            "y": 0,
        }
        self.entities.append(wire_entity) # 将线网实体添加到实体列表

        module_contain_wire={
            "id": str(uuid.uuid4()),
            "human_readable_id": self._get_human_readable_id(),
            "source": parent_module_name,     # 父模块的名称
            "target": wire_entity["title"],   # 当前线网的名称
            "type": "CONTAINS_WIRE",          # 关系类型
            "description": f"{parent_module_name} contains wire {wire_entity['title']}.", # 关系的描述
            "weight": 1, # 可以自定义权重，这里给个默认值
            "combined_degree": 0, # 如果需要，可以在构建完图谱后计算
            "text_unit_ids": [f"{filepath}#{self._get_text_unit_ids(wire)}"], # 关系可能与线网代码位置关联
        }
        self.relationships.append(module_contain_wire)

        self._add_signal_to_map(parent_module_name,wire["name"],wire_entity)

    def _build_register(self, filepath, register):
        """
        构建 Verilog 寄存器 (register) 实体，并添加与父模块的包含关系。

        Args:
            filepath (str): Verilog 文件路径。
            register (dict): 包含寄存器信息的字典。
            parent_module_name (str): 父模块的名称（字符串）。
        """
        # 使用 .get() 方法安全地访问字典键，提供默认值以避免 KeyError
        register_name = register["name"]
        register_msb = register.get('msb', 'N/A')
        register_lsb = register.get('lsb', 'N/A')
        register_signed = register.get('signed', False) # 默认不是有符号的
        register_dimensions = register.get('dimensions', 'N/A')
        register_value = register.get('value', None) # 默认值为 None，表示可能没有初始值
        register_ast = register.get('ast', 'N/A')
        register_startline = register.get('startline', register.get('lineno', -1))
        register_endline = register.get('endline', register.get('lineno', -1))
        parent_module_name=register.get('parent_module','unknown')

        # --- 构建详细的 description 字符串 ---
        description_parts = [
            f"Verilog **register** '{register_name}' is defined within module '{register['parent_module']}' ",
            f"in file '{filepath}' from line {register_startline} to line {register_endline}."
        ]

        # 添加位宽信息
        if register_msb is not None and register_lsb is not None and register_msb != 'N/A' and register_lsb != 'N/A':
            if register_msb == register_lsb:
                description_parts.append(f"It is a **1-bit** signal.")
            else:
                description_parts.append(f"Its **bit-width** is from MSB {register_msb} to LSB {register_lsb}.")
        
        # 添加有无符号信息
        if register_signed:
            description_parts.append(f"It is a **signed** register.")
        else:
            description_parts.append(f"It is an **unsigned** register.")

        # 添加维度信息（如果存在）
        if register_dimensions and register_dimensions != 'N/A':
            description_parts.append(f"It has **dimensions**: {register_dimensions}.")
        
        # 添加初始值信息（如果存在）
        if register_value is not None and register_value != 'None': # 明确检查 None 和字符串 'None'
            description_parts.append(f"It has an **initial value** of '{register_value}'.")
        
        # 添加 AST 节点类型信息
        if register_ast != 'N/A':
             description_parts.append(f"Its **AST node type** is '{register_ast}'.")

        # 将所有描述部分连接成一个完整的字符串
        register_description = " ".join(description_parts)

        # --- 构建寄存器实体字典 ---
        register_entity = {
            "id": str(uuid.uuid4()),
            "human_readable_id": self._get_human_readable_id(),
            "title": register_name,
            "type": "REGISTER",
            "description": register_description,
            "text_unit_ids": [f"{filepath}#{self._get_text_unit_ids(register)}"], # text_unit_ids 通常是列表
            "frequency": 1,
            "degree": 0,
            "x": 0,
            "y": 0,
        }
        self.entities.append(register_entity) # 将寄存器实体添加到实体列表

        # --- 按照你要求的格式添加关系：Module CONTAINS Register ---

        module_contain_register={
            "id": str(uuid.uuid4()),
            "human_readable_id": self._get_human_readable_id(),
            "source": parent_module_name,     # 父模块的名称
            "target": register_entity["title"],   # 当前寄存器的名称
            "type": "CONTAINS_REGISTER",          # 关系类型
            "description": f"{parent_module_name} contains register {register_entity['title']}.", # 关系的描述
            "weight": 1, # 可以自定义权重，这里给个默认值
            "combined_degree": 0, # 如果需要，可以在构建完图谱后计算
            "text_unit_ids": [f"{filepath}#{self._get_text_unit_ids(register)}"], # 关系可能与寄存器代码位置关联  
        }
        self.relationships.append(module_contain_register)   

        self._add_signal_to_map(parent_module_name,register["name"],register_entity)

    def _build_parameter(self, filepath, parameter):
        """
        构建 Verilog 参数 (Parameter) 实体，并添加与父模块的包含关系。

        Args:
            filepath (str): Verilog 文件路径。
            parameter (dict): 包含参数信息的字典，来自 _parse_parameters。
        """
        param_name = parameter.get('name', 'N/A')
        parent_module_name = parameter.get('parent_module', 'unknown')
        param_value = parameter.get('value', 'N/A')
        param_msb = parameter.get('msb', 'N/A')
        param_lsb = parameter.get('lsb', 'N/A')
        param_signed = parameter.get('signed', False)
        param_dimensions = parameter.get('dimensions', [])
        param_ast = parameter.get('ast', 'N/A')
        param_startline = parameter.get('startline', parameter.get('lineno', -1))
        param_endline = parameter.get('endline', parameter.get('lineno', -1))

        # --- 1. 构建 PARAMETER 实体 ---
        description_parts = [
            f"This is a **parameter** '{param_name}' defined in module '{parent_module_name}' ",
            f"in file '{filepath}' from line {param_startline} to line {param_endline}."
        ]

        if param_value != 'N/A':
            description_parts.append(f"Its **value** is '{param_value}'.")
        
        if param_msb != 'N/A' and param_lsb != 'N/A':
            description_parts.append(f"It has a **bit width** from MSB={param_msb} to LSB={param_lsb}.")
        elif param_msb != 'N/A' or param_lsb != 'N/A': # If only one is available, mention it
            description_parts.append(f"It has a **bit width** related to MSB={param_msb} or LSB={param_lsb}.")
        
        if param_signed:
            description_parts.append("It is a **signed** parameter.")
        else:
            description_parts.append("It is an **unsigned** parameter.") # Parameters are often unsigned by default

        if param_dimensions:
            dim_str = ", ".join([f"{dim[0]}:{dim[1]}" for dim in param_dimensions])
            description_parts.append(f"It has **dimensions** {dim_str}.")
        
        if param_ast != 'N/A':
            description_parts.append(f"Its **AST node type** is '{param_ast}'.")

        parameter_entity = {
            "id": str(uuid.uuid4()),
            "human_readable_id": self._get_human_readable_id(),
            "title": param_name, # 包含名称和值，更具描述性
            "type": "PARAMETER",
            "description": " ".join(description_parts),
            "text_unit_ids": [f"{filepath}#{self._get_text_unit_ids(parameter)}"],
            "frequency": 1,
            "degree": 0,
            "x": 0, "y": 0,
        }
        self.entities.append(parameter_entity)

        # --- 2. 构建关系：Module CONTAINS_PARAMETER ---
        self.relationships.append({
            "id": str(uuid.uuid4()),
            "human_readable_id": self._get_human_readable_id(),
            "source": parent_module_name, # 父模块的标题
            "target": parameter_entity["title"],
            "type": "CONTAINS_PARAMETER",
            "description": f"Module '{parent_module_name}' contains parameter '{parameter_entity['title']}'.",
            "weight": 1, # 可以根据重要性调整权重
            "combined_degree": 0,
            "text_unit_ids": [f"{filepath}#{self._get_text_unit_ids(parameter)}"],
        })

        # --- 3. 将参数实体加入 signal_name_to_entity_map ---
        # 尽管是参数，但它也可能在表达式中被引用，作为一种“信号”
        # 所以也将其加入映射，方便后续查找
        self._add_signal_to_map(parent_module_name, param_name, parameter_entity)

    def _build_assign(self, filepath, assign):
        """
        构建 Verilog 赋值语句 (assign) 实体，并添加与父模块的包含关系，
        以及与相关信号的数据流关系。

        Args:
            filepath (str): Verilog 文件路径。
            assign (dict): 包含赋值语句信息的字典。
            parent_module_name (str): 父模块的名称（字符串）。
        """
        assign_startline = assign.get('startline', assign.get('lineno', -1))
        assign_endline = assign.get('endline', assign.get('lineno', -1))
        assign_left = assign.get('left', 'N/A')
        assign_right = assign.get('right', 'N/A')
        assign_ldelay = assign.get('ldelay', None)
        assign_rdelay = assign.get('rdelay', None)
        assign_ast = assign.get('ast', 'N/A')
        parent_module_name=assign.get('parent_module','unknown')

        # --- 1. 构建主 ASSIGNMENT 实体 ---
        description_parts = [
            f"This is an **assignment statement** defined in module '{assign['parent_module']}' ",
            f"in file '{filepath}' from line {assign_startline} to line {assign_endline}."
        ]

        if assign_left != 'N/A' and assign_right != 'N/A':
            description_parts.append(f"The **left-hand side (LHS)** is '{assign_left}' and the **right-hand side (RHS)** is '{assign_right}'.")
        elif assign_left != 'N/A':
            description_parts.append(f"The **left-hand side (LHS)** is '{assign_left}'.")
        elif assign_right != 'N/A':
            description_parts.append(f"The **right-hand side (RHS)** is '{assign_right}'.")
        
        if assign_ldelay is not None:
            description_parts.append(f"It has a **left-hand side (LHS) delay** of '{assign_ldelay}'.")
        if assign_rdelay is not None:
            description_parts.append(f"It has a **right-hand side (RHS) delay** of '{assign_rdelay}'.")
        
        if assign_ast != 'N/A':
            description_parts.append(f"Its **AST node type** is '{assign_ast}'.")

        assign_entity = {
            "id": str(uuid.uuid4()),
            "human_readable_id": self._get_human_readable_id(),
            "title": f"Assign: {assign_left} = {assign_right}", # 使用更具描述性的标题
            "type": "ASSIGNMENT",
            "description": " ".join(description_parts),
            "text_unit_ids": [f"{filepath}#{self._get_text_unit_ids(assign)}"],
            "frequency": 1,
            "degree": 0,
            "x": 0, "y": 0,
        }
        self.entities.append(assign_entity)

        #构建left hand side
        lhs_signal_entity = None
        if assign_left != 'N/A':
            lhs_signal_entity = self._get_signal_entity(parent_module_name, assign_left)
            if lhs_signal_entity is None:
                new_lhs_entity = {
                        "id": str(uuid.uuid4()),
                        "human_readable_id": self._get_human_readable_id(),
                        "title": f"{assign_left}",
                        "type": "LHS_ASSIGN", # 推断为 WIRE
                        "description": (
                            f"An signal '{assign_left}' in module '{parent_module_name}'. "
                            f"It is left hand side in assignment {assign_entity['title']} in file {filepath} from line {assign_startline} to line {assign_endline}."
                        ),
                        "text_unit_ids": [f"{filepath}#{self._get_text_unit_ids(assign)}#LHS"],
                        "frequency": 1, "degree": 0, "x": 0, "y": 0,
                    }
                self.entities.append(new_lhs_entity)
                self._add_signal_to_map(parent_module_name,assign_left,new_lhs_entity)
                lhs_signal_entity = new_lhs_entity # 将新创建的实体赋给 lhs_signal_entity
            else:
                new_desc_part = (
                    f" It is also left hand side in assignment '{assign_entity['title']}' "
                    f"in file '{filepath}' from line {assign_startline} to line {assign_endline}."
                )
                if new_desc_part not in lhs_signal_entity["description"]:
                    lhs_signal_entity["description"] += new_desc_part
                
        #构建left hand side
        rhs_signal_entity = None
        if assign_left != 'N/A':
            rhs_signal_entity = self._get_signal_entity(parent_module_name, assign_right)
            if rhs_signal_entity is None:
                new_rhs_entity = {
                        "id": str(uuid.uuid4()),
                        "human_readable_id": self._get_human_readable_id(),
                        "title": f"{assign_right}",
                        "type": "RHS_ASSIGN", # 推断为 WIRE
                        "description": (
                            f"An signal '{assign_right}' in module '{parent_module_name}'. "
                            f"It is right hand side in assignment {assign_entity['title']} in file {filepath} from line {assign_startline} to line {assign_endline}."
                        ),
                        "text_unit_ids": [f"{filepath}#{self._get_text_unit_ids(assign)}#RHS"],
                        "frequency": 1, "degree": 0, "x": 0, "y": 0,
                    }
                self.entities.append(new_rhs_entity)
                self._add_signal_to_map(parent_module_name,assign_right,new_rhs_entity)
                rhs_signal_entity = new_rhs_entity # 将新创建的实体赋给 rhs_signal_entity
            else:
                new_desc_part = (
                    f" It is also right hand side in assignment '{assign_entity['title']}' "
                    f"in file '{filepath}' from line {assign_startline} to line {assign_endline}."
                )
                if new_desc_part not in rhs_signal_entity["description"]:
                    rhs_signal_entity["description"] += new_desc_part  

        assert(lhs_signal_entity is not None and rhs_signal_entity is not None)  
        # --- 2. 构建关系 ---

        # 关系 A: Module CONTAINS Assignment (模块包含赋值语句)
        self.relationships.append({
            "id": str(uuid.uuid4()),
            "human_readable_id": self._get_human_readable_id(),
            "source": parent_module_name,
            "target": assign_entity["title"],
            "type": "CONTAINS_ASSIGNMENT",
            "description": f"Module '{parent_module_name}' contains assignment '{assign_entity['title']}'.",
            "weight": 1, "combined_degree": 0,
            "text_unit_ids": [f"{filepath}#{self._get_text_unit_ids(assign)}"],
        })

        self.relationships.append({
            "id": str(uuid.uuid4()),
            "human_readable_id": self._get_human_readable_id(),
            "source": assign_entity['title'],
            "target": lhs_signal_entity["title"],
            "type": "ASSIGNMENT_LHS",
            "description": f"{assign_entity['title']} has left hand side {lhs_signal_entity['title']}",
            "weight": 1, "combined_degree": 0,
            "text_unit_ids": [f"{filepath}#{self._get_text_unit_ids(assign)}#lhs"],
        })

        self.relationships.append({
            "id": str(uuid.uuid4()),
            "human_readable_id": self._get_human_readable_id(),
            "source": assign_entity['title'],
            "target": rhs_signal_entity["title"],
            "type": "ASSIGNMENT_RHS",
            "description": f"{assign_entity['title']} has right hand side {rhs_signal_entity['title']}",
            "weight": 1, "combined_degree": 0,
            "text_unit_ids": [f"{filepath}#{self._get_text_unit_ids(assign)}#rhs"],
        })

        # 关系 B: Data Flow - RHS DRIVES LHS (右侧驱动左侧)
        # 这里的 source 和 target 直接使用 assign['right'] 和 assign['left'] 的名称。
        # 假设这些名称能够与图谱中已有的 PORT/WIRE/REGISTER 实体匹配。
        if assign_left != 'N/A' and assign_right != 'N/A':
            self.relationships.append({
                "id": str(uuid.uuid4()),
                "human_readable_id": self._get_human_readable_id(),
                "source": f"{rhs_signal_entity['title']}", # 赋值的源头（通常是信号名或表达式）
                "target": f"{lhs_signal_entity['title']}",   # 赋值的目标（通常是信号名）
                "type": "DRIVES",       # 关系类型：表示数据流从源头驱动目标
                "description": f"The expression/signal '{assign_right}' **drives** the signal '{assign_left}' via assignment '{assign_entity['title']}'.",
                "weight": 2, # 数据流关系通常比包含关系更重要，可以给更高权重
                "combined_degree": 0,
                "text_unit_ids": [f"{filepath}#{self._get_text_unit_ids(assign)}"],
            })

    # 这个里面存在大问题 
    def _build_instance(self, filepath, instance):
        """
        构建 Verilog 模块实例 (instance) 实体，并添加与父模块的包含关系，
        以及与其他模块的实例化关系。

        Args:
            filepath (str): Verilog 文件路径。
            instance (dict): 包含实例信息的字典。
            parent_module_name (str): 父模块的名称（字符串）。
        """
        instance_name = instance.get('instance_name', 'N/A')
        module_name_instantiated = instance.get('module_name', 'N/A') # 被实例化的模块名
        instance_startline = instance.get('startline', instance.get('lineno', -1))
        instance_endline = instance.get('endline', instance.get('lineno', -1))
        port_connections = instance.get('port_connections', [])
        parameter_connections = instance.get('parameter_connections', [])
        arrays = instance.get('arrays', {'msb': 'N/A', 'lsb': 'N/A'}) # array信息，包含msb和lsb
        ast = instance.get('ast', 'N/A')
        parent_module_name=instance.get('parent_module','unknown')

        # --- 1. 构建 INSTANCE 实体 ---
        description_parts = [
            f"This is an **instance** '{instance_name}' of module '{module_name_instantiated}', ",
            f"defined within module '{instance['parent_module']}' in file '{filepath}' ",
            f"from line {instance_startline} to line {instance_endline}."
        ]
        
        if arrays and (arrays.get('msb') != 'N/A' or arrays.get('lsb') != 'N/A'):
             description_parts.append(f"It is an array instance with dimensions from MSB {arrays['msb']} to LSB {arrays['lsb']}.")

        if port_connections:
            description_parts.append(f"It has {len(port_connections)} port connections.")
        if parameter_connections:
            description_parts.append(f"It has {len(parameter_connections)} parameter overrides.")
        if ast != 'N/A':
            description_parts.append(f"Its **AST node type** is '{ast}'.")

        instance_entity = {
            "id": str(uuid.uuid4()),
            "human_readable_id": self._get_human_readable_id(),
            "title": f"Instance: {instance_name} ({module_name_instantiated})", # 使用更具描述性的标题
            "type": "INSTANCE",
            "description": " ".join(description_parts),
            "text_unit_ids": [f"{filepath}#{self._get_text_unit_ids(instance)}"],
            "frequency": 1,
            "degree": 0,
            "x": 0, "y": 0,
        }
        self.entities.append(instance_entity)

        # --- 2. 构建关系 ---

        # 关系 A: Module CONTAINS Instance (父模块包含此实例)
        self.relationships.append({
            "id": str(uuid.uuid4()),
            "human_readable_id": self._get_human_readable_id(),
            "source": parent_module_name,
            "target": instance_entity["title"],
            "type": "CONTAINS_INSTANCE",
            "description": f"Module '{parent_module_name}' contains instance '{instance_entity['title']}'.",
            "weight": 1, "combined_degree": 0,
            "text_unit_ids": [f"{filepath}#{self._get_text_unit_ids(instance)}"],
        })

        # 关系 B: Instance INSTANTIATES Module (实例实例化了另一个模块)
        # 这里 module_name_instantiated 应该是你图谱中另一个 MODULE 实体的 'title'
        self.relationships.append({
            "id": str(uuid.uuid4()),
            "human_readable_id": self._get_human_readable_id(),
            "source": instance_entity["title"],
            "target": module_name_instantiated, # 被实例化的模块名称
            "type": "INSTANTIATES",
            "description": f"Instance '{instance_entity['title']}' **instantiates** module '{module_name_instantiated}'.",
            "weight": 2, # 实例化关系通常很重要
            "combined_degree": 0,
            "text_unit_ids": [f"{filepath}#{self._get_text_unit_ids(instance)}"],
        })

        # 关系 C: Port Connections (实例的端口连接)
        for port_conn in port_connections:
            port_name = port_conn.get("portname", "N/A") # 被实例化模块的端口名称
            arg_name = port_conn.get("argname", "N/A")   # 父模块中连接的信号名称

            # 这里不用管，因为arg_name一定是父模块中的一个信号
            arg_entity=self._get_signal_entity(parent_module_name,arg_name)
            assert(arg_entity is not None)
            new_desc_part = (
                    f" It is also a arg in instance '{instance_entity['title']}' "
                )
            if new_desc_part not in arg_entity["description"]:
                    arg_entity["description"] += new_desc_part
            if port_name != 'N/A' and arg_name != 'N/A':
                # 关系类型可以考虑：
                # 1. INSTANCE_PORT_MAPS_TO (实例的端口映射到父模块的信号)
                # 2. CONNECTS_TO (更通用的连接，源可以是实例内部端口，目标是外部信号)
                # 3. DRIVES / DRIVEN_BY （如果能判断方向）

                # 考虑使用 INSTANCE_CONNECTS_TO_SIGNAL，或者更具体的 PORT_CONNECTED_TO_SIGNAL
                # 这里我们假设 arg_name 是父模块中某个信号的名称 (PORT, WIRE, REGISTER)
                
                # 从实例的端口到父模块的信号
                self.relationships.append({
                    "id": str(uuid.uuid4()),
                    "human_readable_id": self._get_human_readable_id(),
                    "source": port_name, # 更明确的实例内部端口概念
                    "target": arg_name, # 父模块中的信号名称
                    "type": "CONNECTS_TO", # 简单通用的连接关系
                    "description": f"Instance '{instance_name}'s port '{port_name}' **connects to** signal '{arg_name}' in module '{parent_module_name}'.",
                    "weight": 1, "combined_degree": 0,
                    "text_unit_ids": [f"{filepath}#{self._get_text_unit_ids(instance)}"],
                })

        # 关系 D: Parameter Overrides (参数覆盖)
        for param_conn in parameter_connections:
            param_name = param_conn.get("paramname", "N/A") # 被实例化模块的参数名
            arg_value = param_conn.get("argname", "N/A")    # 实例化的值

            arg_entity=self._get_signal_entity(parent_module_name,arg_value)
            assert(arg_entity is not None)
            new_desc_part = (
                    f" It is also a parameter arg in instance '{instance_entity['title']}' "
                )
            if new_desc_part not in arg_entity["description"]:
                    arg_entity["description"] += new_desc_part
            if param_name != 'N/A' and arg_value != 'N/A':
                self.relationships.append({
                    "id": str(uuid.uuid4()),
                    "human_readable_id": self._get_human_readable_id(),
                    "source": instance_entity["title"], # 实例实体
                    "target": param_name, # 被实例化模块的参数概念
                    "type": "OVERRIDE_PARAMETER",
                    "description": f"Instance '{instance_entity['title']}' **overrides** parameter '{param_name}' of module '{module_name_instantiated}' with value '{arg_value}'.",
                    "weight": 1, "combined_degree": 0,
                    "text_unit_ids": [f"{filepath}#{self._get_text_unit_ids(instance)}"],
                })
        
    def _build_always_block(self, filepath, always_block):
        """
        构建 Verilog Always Block 实体，并添加其内部的控制流和赋值信息。

        Args:
            filepath (str): Verilog 文件路径。
            always_block (dict): 包含 Always Block 信息的字典，来自 _parse_always_blocks。
            parent_module_name (str): Always Block 所属父模块的名称。
        """
        lineno = always_block.get('lineno', -1)
        startline = always_block.get('startline', lineno)
        endline = always_block.get('endline', lineno)
        sens_list = always_block.get('senlist', [])
        logic_type = always_block.get('logic_type', 'unknown')
        ast = always_block.get('ast', 'Always')
        cfg_data = always_block.get('cfg_data', {}) # 关键数据，包含 target: condition -> assignment

        senslist_summary = self._get_senslist_summary(sens_list)
        parent_module_name=always_block['parent_module']
        # --- 1. 构建 ALWAYS_BLOCK 实体 ---
        always_block_entity = {
            "id": str(uuid.uuid4()),
            "human_readable_id": self._get_human_readable_id(),
            "title": f"Always Block ({logic_type}) @ ({senslist_summary})",
            "type": "ALWAYS_BLOCK",
            "description": (
                f"An **always block** ({logic_type} logic) in module '{parent_module_name}' "
                f"from file '{filepath}' lines {startline}-{endline}. "
                f"It is sensitive to: {senslist_summary}. "
                f"Its AST node type is '{ast}'."
            ),
            "text_unit_ids": [f"{filepath}#{self._get_text_unit_ids(always_block)}"],
            "frequency": 1, "degree": 0, "x": 0, "y": 0,
        }
        self.entities.append(always_block_entity)

        # --- 2. 构建关系 A: Module CONTAINS Always Block ---
        self.relationships.append({
            "id": str(uuid.uuid4()),
            "human_readable_id": self._get_human_readable_id(),
            "source": parent_module_name, # 父模块实体标题
            "target": always_block_entity["title"],
            "type": "CONTAINS_ALWAYS_BLOCK",
            "description": f"Module '{parent_module_name}' contains always block '{always_block_entity['title']}'.",
            "weight": 1, "combined_degree": 0,
            "text_unit_ids": [f"{filepath}#{self._get_text_unit_ids(always_block)}"],
        })

        # --- 3. 构建关系 B: ALWAYS_BLOCK HAS_SENSITIVE_SIGNAL ---
        # always 块对哪些信号敏感
        for sen_item in sens_list:
            sensitive_signal_name = sen_item.get('sig')
            edge_type = sen_item.get('edge')
            if sensitive_signal_name:
                # 尝试链接到已存在的信号实体（PORT, WIRE, REGISTER）
                sensitive_signal_entity=self._get_signal_entity(parent_module_name,sensitive_signal_name)
                assert(sensitive_signal_entity is not None)
                self.relationships.append({
                    "id": str(uuid.uuid4()),
                    "human_readable_id": self._get_human_readable_id(),
                    "source": always_block_entity["title"],
                    "target": sensitive_signal_entity['title'], # 如果找到实体，则链接到实体；否则链接到名称字符串
                    "type": "HAS_SENSITIVE_SIGNAL",
                    "description": (
                        f"Always block '{always_block_entity['title']}' is sensitive to "
                        f"{edge_type + ' ' if edge_type else ''}signal '{sensitive_signal_name}'."
                    ),
                    "weight": 1, "combined_degree": 0,
                    "text_unit_ids": [f"{filepath}#{self._get_text_unit_ids(always_block)}# sens_{sensitive_signal_name}"],
                })
                new_desc_part = f" It is also a sensitive signal within an always block in module '{parent_module_name}'."
                if new_desc_part not in sensitive_signal_entity["description"]:
                    sensitive_signal_entity["description"] += new_desc_part

        # --- 4. 遍历 cfg_data 构建内部的 CONTROL_FLOW_CONDITION 和 INTERNAL_ASSIGNMENT 实体及关系 ---
        # cfg_data 包含了 always 块内部的条件和赋值逻辑
        for target_signal_name, assignments in cfg_data.items():
            lhs_signal_entity = self._get_signal_entity(parent_module_name, target_signal_name)
            if lhs_signal_entity is None:
            # 如果 LHS 信号不存在，我们在这里创建一个。
            # always 块内部的左值通常是 register
                lhs_signal_entity = {
                    "id": str(uuid.uuid4()),
                    "human_readable_id": self._get_human_readable_id(),
                    "title": target_signal_name,
                    "type": "LHS_ALWASY", # 内部赋值的 LHS 通常是 REGISTER
                    "description": (
                        f"It is a left hand side in always block which is in {parent_module_name} in {filepath} from line {startline} to line {endline}"
                    ),
                    "text_unit_ids": [f"{filepath}#LHS_ALWAYS_{target_signal_name}"],
                    "frequency": 1, "degree": 0, "x": 0, "y": 0,
                }
                self.entities.append(lhs_signal_entity)
                self._add_signal_to_map(parent_module_name, target_signal_name, lhs_signal_entity)
            else:
                new_desc_part = f" It is also driven as the left-hand side within an always block in module '{parent_module_name}'."
                if new_desc_part not in lhs_signal_entity["description"]:
                    lhs_signal_entity["description"] += new_desc_part
            
            self.relationships.append({
                "id": str(uuid.uuid4()),
                "human_readable_id": self._get_human_readable_id(),
                "source": always_block_entity["title"],
                "target": lhs_signal_entity["title"],
                "type": "OUTPUTS_SIGNAL_VIA_LHS",
                "description": f"Always block '{always_block_entity['title']}' assigns values to signal '{lhs_signal_entity['title']}'.",
                "weight": 2, "combined_degree": 0,
                "text_unit_ids": [f"{filepath}#always_output_{target_signal_name}"],
            })
            for assign_info in assignments:
                condition_expr = assign_info.get('condition')
                assign_line = assign_info.get('line')
                right_expr = assign_info.get('right_expr')
                assignment_type = assign_info.get('assignment_type')
                rhs_signal_entity = self._get_signal_entity(parent_module_name, right_expr)
                if rhs_signal_entity is None:
                # 如果 LHS 信号不存在，我们在这里创建一个。
                # always 块内部的左值通常是 register
                    rhs_signal_entity = {
                        "id": str(uuid.uuid4()),
                        "human_readable_id": self._get_human_readable_id(),
                        "title": right_expr,
                        "type": "RHS_ALWASY", # 内部赋值的 LHS 通常是 REGISTER
                        "description": (
                            f"It is a right hand side in always block which is at {assign_line} in {parent_module_name} in {filepath} from line {startline} to line {endline}"
                        ),
                        "text_unit_ids": [f"{filepath}#RHS_ALWAYS_{target_signal_name}"],
                        "frequency": 1, "degree": 0, "x": 0, "y": 0,
                    }
                    self.entities.append(rhs_signal_entity)
                    self._add_signal_to_map(parent_module_name, right_expr, rhs_signal_entity)
                else:
                    new_desc_part = f" It is also  as the left-hand side within an always block at line {assign_line} in module '{parent_module_name}'."
                    if new_desc_part not in rhs_signal_entity["description"]:
                        rhs_signal_entity["description"] += new_desc_part

                self.relationships.append({
                    "id": str(uuid.uuid4()),
                    "human_readable_id": self._get_human_readable_id(),
                    "source": rhs_signal_entity["title"],
                    "target": lhs_signal_entity["title"],
                    "type": assignment_type,
                    "description": f"In always block '{always_block_entity['title']}' {rhs_signal_entity['title']} is assigned to {lhs_signal_entity['title']},the assignment condition is {condition_expr}",
                    "weight": 2, "combined_degree": 0,
                    "text_unit_ids": [f"{filepath}#always_output_{target_signal_name}"],
                })
        
        
    def _build_kg(self):
        for filepath in self.rtl_info.parsed_data.keys():
            for module in self.rtl_info.parsed_data[filepath]["modules"]:
                #Add module node to G
                self._build_module(filepath,module)
                #Add nodes for module ports, signals, instances, FSMs
                for port in self.rtl_info.parsed_data[filepath]["ports"]:
                    if port["parent_module"] == module["name"]:
                        self._build_port(filepath,port)
                for wire in self.rtl_info.parsed_data[filepath]["wires"]:
                    if wire["parent_module"]==module["name"]:
                        self._build_wire(filepath,wire)
                for register in self.rtl_info.parsed_data[filepath]["registers"]:
                    if register["parent_module"]==module["name"]:
                        self._build_register(filepath,register)
                for assign in self.rtl_info.parsed_data[filepath]["assigns"]:
                    if assign["parent_module"]==module["name"]:
                        self._build_assign(filepath,assign)
                for instance in self.rtl_info.parsed_data[filepath]["instances"]:
                    if instance["parent_module"]==module["name"]:
                        self._build_instance(filepath,instance)
                for always_block in self.rtl_info.parsed_data[filepath]["always_blocks"]:
                    if always_block["parent_module"]==module["name"]:
                        self._build_always_block(filepath,always_block)
                
    def _to_json(self,data,indent=2):
        return json.dumps(data,indent=indent,default=str)
    
    def get_kg(self):
        self._build_kg()
        from KG_vis import visualize_graph_from_data
        visualize_graph_from_data(self.entities,self.relationships)
        return self._to_json(self.entities),self._to_json(self.relationships)

    
