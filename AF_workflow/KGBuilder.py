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
    
    def _add_signal_to_map(self, signal_name, signal_entity, parent_module_name):
        key = (parent_module_name, signal_name)
        self.signal_name_to_entity_map[key] = signal_entity

    def _get_signal_entity(self, signal_name, parent_module_name):
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
        parent_module=port.get('parent_module','unknown')

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
            "source": parent_module,     # 父模块的名称
            "target": port_entity["title"],   # 当前端口的名称
            "type": "CONTAINS_PORT",          # 关系类型
            "description": f"{parent_module} contains port {port_entity['title']}.", # 关系的描述
            "weight": 1, # 可以自定义权重，这里给个默认值
            "combined_degree": 0, # 如果需要，可以在构建完图谱后计算
            "text_unit_ids": [f"{filepath}#{self._get_text_unit_ids(port)}"], # 关系可能与端口代码位置关联
        }
        self.relationships.append(module_contain_port)
        return port_entity # 返回端口实体，以便后续可能需要它的 ID
    
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

        # 关系 B: Data Flow - RHS DRIVES LHS (右侧驱动左侧)
        # 这里的 source 和 target 直接使用 assign['right'] 和 assign['left'] 的名称。
        # 假设这些名称能够与图谱中已有的 PORT/WIRE/REGISTER 实体匹配。
        if assign_left != 'N/A' and assign_right != 'N/A':
            self.relationships.append({
                "id": str(uuid.uuid4()),
                "human_readable_id": self._get_human_readable_id(),
                "source": assign_right, # 赋值的源头（通常是信号名或表达式）
                "target": assign_left,   # 赋值的目标（通常是信号名）
                "type": "DRIVES",       # 关系类型：表示数据流从源头驱动目标
                "description": f"The expression/signal '{assign_right}' **drives** the signal '{assign_left}' via assignment '{assign_entity['title']}'.",
                "weight": 2, # 数据流关系通常比包含关系更重要，可以给更高权重
                "combined_degree": 0,
                "text_unit_ids": [f"{filepath}#{self._get_text_unit_ids(assign)}"],
            })
        
        # 关系 C: Assignment MODIFIES LHS (赋值语句修改了左侧信号) - 这是一个更直接的事件关系
        # 或者使用 USES_LHS / USES_RHS，更明确赋值这个行为本身和信号的交互。
        if assign_left != 'N/A':
            self.relationships.append({
                "id": str(uuid.uuid4()),
                "human_readable_id": self._get_human_readable_id(),
                "source": assign_entity["title"], # 赋值语句本身
                "target": assign_left,            # 被修改的信号
                "type": "MODIFIES_SIGNAL",        # 关系类型：赋值语句修改了信号
                "description": f"Assignment '{assign_entity['title']}' **modifies** the signal '{assign_left}'.",
                "weight": 1, "combined_degree": 0,
                "text_unit_ids": [f"{filepath}#{self._get_text_unit_ids(assign)}#LHS"],
            })

        # 关系 D: Assignment USES RHS (赋值语句使用了右侧表达式/信号)
        if assign_right != 'N/A':
            self.relationships.append({
                "id": str(uuid.uuid4()),
                "human_readable_id": self._get_human_readable_id(),
                "source": assign_entity["title"],  # 赋值语句本身
                "target": assign_right,            # 使用的信号/表达式
                "type": "USES_EXPRESSION_OR_SIGNAL", # 关系类型：赋值语句使用了某个表达式或信号
                "description": f"Assignment '{assign_entity['title']}' **uses** the expression/signal '{assign_right}' as its source.",
                "weight": 1, "combined_degree": 0,
                "text_unit_ids": [f"{filepath}#{self._get_text_unit_ids(assign)}#RHS"],
            })


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
                    "source": f"Instance Port: {instance_name}.{port_name}", # 更明确的实例内部端口概念
                    "target": arg_name, # 父模块中的信号名称
                    "type": "CONNECTS_TO", # 简单通用的连接关系
                    "description": f"Instance '{instance_name}'s port '{port_name}' **connects to** signal '{arg_name}' in module '{parent_module_name}'.",
                    "weight": 1, "combined_degree": 0,
                    "text_unit_ids": [f"{filepath}#{self._get_text_unit_ids(instance)}"],
                })

                # 你也可以进一步添加从父模块信号到实例端口的连接，取决于你如何建模信号流
                # 例如: (arg_name) -> CONNECTS_TO_INSTANCE_PORT -> (f"Instance Port: {instance_name}.{port_name}")


        # 关系 D: Parameter Overrides (参数覆盖)
        for param_conn in parameter_connections:
            param_name = param_conn.get("paramname", "N/A") # 被实例化模块的参数名
            arg_value = param_conn.get("argname", "N/A")    # 实例化的值

            if param_name != 'N/A' and arg_value != 'N/A':
                self.relationships.append({
                    "id": str(uuid.uuid4()),
                    "human_readable_id": self._get_human_readable_id(),
                    "source": instance_entity["title"], # 实例实体
                    "target": f"Parameter: {module_name_instantiated}.{param_name}", # 被实例化模块的参数概念
                    "type": "OVERRIDE_PARAMETER",
                    "description": f"Instance '{instance_entity['title']}' **overrides** parameter '{param_name}' of module '{module_name_instantiated}' with value '{arg_value}'.",
                    "weight": 1, "combined_degree": 0,
                    "text_unit_ids": [f"{filepath}#{self._get_text_unit_ids(instance)}"],
                })
        
    # def _build_always_block(self, filepath, always_block):
    #     """
    #     构建 Verilog Always Block 实体，并添加其内部的控制流和赋值信息。

    #     Args:
    #         filepath (str): Verilog 文件路径。
    #         always_block (dict): 包含 Always Block 信息的字典，来自 _parse_always_blocks。
    #         parent_module_name (str): Always Block 所属父模块的名称。
    #     """
    #     lineno = always_block.get('lineno', -1)
    #     startline = always_block.get('startline', lineno)
    #     endline = always_block.get('endline', lineno)
    #     sens_list = always_block.get('senlist', [])
    #     logic_type = always_block.get('logic_type', 'unknown')
    #     ast = always_block.get('ast', 'Always')
    #     cfg_data = always_block.get('cfg_data', {}) # 关键数据，包含 target: condition -> assignment

    #     senslist_summary = self._get_senslist_summary(sens_list)
    #     parent_module_name=always_block['parent_module']
    #     # --- 1. 构建 ALWAYS_BLOCK 实体 ---
    #     always_block_entity = {
    #         "id": str(uuid.uuid4()),
    #         "human_readable_id": self._get_human_readable_id(),
    #         "title": f"Always Block ({logic_type}) @ ({senslist_summary})",
    #         "type": "ALWAYS_BLOCK",
    #         "description": (
    #             f"An **always block** ({logic_type} logic) in module '{parent_module_name}' "
    #             f"from file '{filepath}' lines {startline}-{endline}. "
    #             f"It is sensitive to: {senslist_summary}. "
    #             f"Its AST node type is '{ast}'."
    #         ),
    #         "text_unit_ids": [f"{filepath}#{self._get_text_unit_ids(always_block)}"],
    #         "frequency": 1, "degree": 0, "x": 0, "y": 0,
    #     }
    #     self.entities.append(always_block_entity)

    #     # --- 2. 构建关系 A: Module CONTAINS Always Block ---
    #     self.relationships.append({
    #         "id": str(uuid.uuid4()),
    #         "human_readable_id": self._get_human_readable_id(),
    #         "source": parent_module_name, # 父模块实体标题
    #         "target": always_block_entity["title"],
    #         "type": "CONTAINS_ALWAYS_BLOCK",
    #         "description": f"Module '{parent_module_name}' contains always block '{always_block_entity['title']}'.",
    #         "weight": 1, "combined_degree": 0,
    #         "text_unit_ids": [f"{filepath}#{self._get_text_unit_ids(always_block)}"],
    #     })

    #     # --- 3. 构建关系 B: ALWAYS_BLOCK HAS_SENSITIVE_SIGNAL ---
    #     # always 块对哪些信号敏感
    #     for sen_item in sens_list:
    #         sensitive_signal_name = sen_item.get('sig')
    #         edge_type = sen_item.get('edge')
    #         if sensitive_signal_name:
    #             # 尝试链接到已存在的信号实体（PORT, WIRE, REGISTER）
    #             sensitive_signal_entity_title = self._get_signal_entity_title_by_name(sensitive_signal_name, parent_module_name)
                
    #             self.relationships.append({
    #                 "id": str(uuid.uuid4()),
    #                 "human_readable_id": self._get_human_readable_id(),
    #                 "source": always_block_entity["title"],
    #                 "target": sensitive_signal_entity_title if sensitive_signal_entity_title else sensitive_signal_name, # 如果找到实体，则链接到实体；否则链接到名称字符串
    #                 "type": "HAS_SENSITIVE_SIGNAL",
    #                 "description": (
    #                     f"Always block '{always_block_entity['title']}' is sensitive to "
    #                     f"{edge_type + ' ' if edge_type else ''}signal '{sensitive_signal_name}'."
    #                 ),
    #                 "weight": 1, "combined_degree": 0,
    #                 "text_unit_ids": [f"{filepath}#{self._get_text_unit_ids(always_block, f'sens_{sensitive_signal_name}')}"],
    #             })
        
    #     # --- 4. 遍历 cfg_data 构建内部的 CONTROL_FLOW_CONDITION 和 INTERNAL_ASSIGNMENT 实体及关系 ---
    #     # cfg_data 包含了 always 块内部的条件和赋值逻辑
    #     for target_signal_name, assignments in cfg_data.items():
    #         for assign_info in assignments:
    #             condition_expr = assign_info.get('condition')
    #             assign_line = assign_info.get('line')
    #             right_expr = assign_info.get('right_expr')
    #             assignment_type = assign_info.get('assignment_type')

    #             # 构建 CONTROL_FLOW_CONDITION 实体
    #             # 对相同的条件表达式进行去重，避免冗余实体
    #             condition_title = f"Condition: {condition_expr}" 
    #             if condition_expr not in self._condition_entity_map:
    #                 condition_entity = {
    #                     "id": str(uuid.uuid4()),
    #                     "human_readable_id": self._get_human_readable_id(),
    #                     "title": condition_title,
    #                     "type": "CONTROL_FLOW_CONDITION",
    #                     "description": (
    #                         f"Control flow condition '{condition_expr}' within an always block, "
    #                         f"defined in module '{parent_module_name}' in file '{filepath}' at line {assign_line}. "
    #                         f"This condition leads to assignments of '{target_signal_name}'."
    #                     ),
    #                     "text_unit_ids": [f"{filepath}#{self._get_text_unit_ids(assign_info, f'cond_{condition_expr}')}"],
    #                     "frequency": 1, "degree": 0, "x": 0, "y": 0,
    #                 }
    #                 self.entities.append(condition_entity)
    #                 self._condition_entity_map[condition_expr] = condition_entity
    #             else:
    #                 condition_entity = self._condition_entity_map[condition_expr]
                
    #             # 构建 INTERNAL_ASSIGNMENT 实体
    #             # 代表 always 块内部的每一次具体赋值行为
    #             internal_assign_title = f"Internal Assign: {target_signal_name} {assignment_type} {right_expr}"
    #             internal_assign_entity = {
    #                 "id": str(uuid.uuid4()),
    #                 "human_readable_id": self._get_human_readable_id(),
    #                 "title": internal_assign_title,
    #                 "type": "INTERNAL_ASSIGNMENT",
    #                 "description": (
    #                     f"An internal assignment within an always block: '{target_signal_name}' {assignment_type} '{right_expr}'. "
    #                     f"Defined in module '{parent_module_name}' in file '{filepath}' at line {assign_line}. "
    #                     f"This assignment is {assignment_type} and affects '{target_signal_name}'."
    #                 ),
    #                 "text_unit_ids": [f"{filepath}#{self._get_text_unit_ids(assign_info, f'assign_{target_signal_name}_{assign_line}')}"],
    #                 "frequency": 1, "degree": 0, "x": 0, "y": 0,
    #             }
    #             self.entities.append(internal_assign_entity)

    #             # 关系 C: Always Block CONTROLS_BY_CONDITION Control Flow Condition
    #             # always 块包含某个条件逻辑
    #             self.relationships.append({
    #                 "id": str(uuid.uuid4()),
    #                 "human_readable_id": self._get_human_readable_id(),
    #                 "source": always_block_entity["title"],
    #                 "target": condition_entity["title"],
    #                 "type": "CONTROLS_BY_CONDITION",
    #                 "description": f"Always block '{always_block_entity['title']}' includes control flow based on condition '{condition_entity['title']}'.",
    #                 "weight": 1, "combined_degree": 0,
    #                 "text_unit_ids": [f"{filepath}#{self._get_text_unit_ids(assign_info, f'block_cond_{condition_expr}')}"],
    #             })

    #             # 关系 D: Control Flow Condition LEADS_TO_ASSIGNMENT Internal Assignment
    #             # 特定条件导致内部赋值发生
    #             self.relationships.append({
    #                 "id": str(uuid.uuid4()),
    #                 "human_readable_id": self._get_human_readable_id(),
    #                 "source": condition_entity["title"],
    #                 "target": internal_assign_entity["title"],
    #                 "type": "LEADS_TO_ASSIGNMENT",
    #                 "description": f"Condition '{condition_entity['title']}' leads to internal assignment '{internal_assign_entity['title']}'.",
    #                 "weight": 1, "combined_degree": 0,
    #                 "text_unit_ids": [f"{filepath}#{self._get_text_unit_ids(assign_info, f'cond_assign_{target_signal_name}_{assign_line}')}"],
    #             })

    #             # 关系 E: Internal Assignment MODIFIES_SIGNAL_IN_BLOCK
    #             # 内部赋值修改了哪个信号（左值）
    #             # 尝试链接到已存在的信号实体
    #             target_signal_entity_title = self._get_signal_entity_title_by_name(target_signal_name, parent_module_name)
    #             if target_signal_entity_title:
    #                 self.relationships.append({
    #                     "id": str(uuid.uuid4()),
    #                     "human_readable_id": self._get_human_readable_id(),
    #                     "source": internal_assign_entity["title"],
    #                     "target": target_signal_entity_title, # 链接到已存在的信号实体
    #                     "type": "MODIFIES_SIGNAL_IN_BLOCK",
    #                     "description": f"Internal assignment '{internal_assign_entity['title']}' **modifies** signal '{target_signal_name}'.",
    #                     "weight": 2,
    #                     "combined_degree": 0,
    #                     "text_unit_ids": [f"{filepath}#{self._get_text_unit_ids(assign_info, f'modifies_{target_signal_name}')}"],
    #                 })
    #             else: 
    #                 # 如果目标信号未被实体化（可能是不常见的形式或者解析遗漏）
    #                 self.relationships.append({
    #                     "id": str(uuid.uuid4()),
    #                     "human_readable_id": self._get_human_readable_id(),
    #                     "source": internal_assign_entity["title"],
    #                     "target": target_signal_name, # 直接使用字符串名称
    #                     "type": "MODIFIES_UNRESOLVED_SIGNAL_IN_BLOCK", 
    #                     "description": f"Internal assignment '{internal_assign_entity['title']}' **modifies** an unresolved signal/expression '{target_signal_name}'.",
    #                     "weight": 0.5,
    #                     "combined_degree": 0,
    #                     "text_unit_ids": [f"{filepath}#{self._get_text_unit_ids(assign_info, f'modifies_unres_{target_signal_name}')}"],
    #                 })

    #             # 关系 F: Internal Assignment USES_SIGNAL_IN_BLOCK / USES_LITERAL_OR_EXPRESSION_IN_BLOCK
    #             # 内部赋值使用了哪个信号或表达式（右值）
    #             if right_expr:
    #                 source_signal_entity_title = self._get_signal_entity_title_by_name(right_expr, parent_module_name)
    #                 if source_signal_entity_title: # 如果右侧表达式是某个已定义的信号
    #                     self.relationships.append({
    #                         "id": str(uuid.uuid4()),
    #                         "human_readable_id": self._get_human_readable_id(),
    #                         "source": internal_assign_entity["title"],
    #                         "target": source_signal_entity_title, # 链接到已存在的信号实体
    #                         "type": "USES_SIGNAL_IN_BLOCK",
    #                         "description": f"Internal assignment '{internal_assign_entity['title']}' **uses** signal '{right_expr}'.",
    #                         "weight": 1,
    #                         "combined_degree": 0,
    #                         "text_unit_ids": [f"{filepath}#{self._get_text_unit_ids(assign_info, f'uses_{right_expr}')}"],
    #                     })
    #                 else: # 如果右侧表达式是字面量、常量或复杂表达式，不能直接映射到单个信号
    #                     self.relationships.append({
    #                         "id": str(uuid.uuid4()),
    #                         "human_readable_id": self._get_human_readable_id(),
    #                         "source": internal_assign_entity["title"],
    #                         "target": right_expr, # 目标是右侧表达式的字符串值
    #                         "type": "USES_LITERAL_OR_EXPRESSION_IN_BLOCK",
    #                         "description": f"Internal assignment '{internal_assign_entity['title']}' **uses** literal/expression '{right_expr}'.",
    #                         "weight": 0.8,
    #                         "combined_degree": 0,
    #                         "text_unit_ids": [f"{filepath}#{self._get_text_unit_ids(assign_info, f'uses_lit_expr_{right_expr}')}"],
    #                     })
                    
    #                 # 关系 G (可选): DRIVES_IN_BLOCK - 内部数据流关系
    #                 # 如果左右值都是已解析的信号实体，则可以建立数据流关系
    #                 if target_signal_entity_title and source_signal_entity_title:
    #                     self.relationships.append({
    #                         "id": str(uuid.uuid4()),
    #                         "human_readable_id": self._get_human_readable_id(),
    #                         "source": source_signal_entity_title, # 源是驱动信号实体
    #                         "target": target_signal_entity_title, # 目标是被驱动信号实体
    #                         "type": "DRIVES_IN_BLOCK", # 明确是 always 块内部的数据流
    #                         "description": f"Signal '{source_signal_entity_title}' **drives** signal '{target_signal_entity_title}' via internal assignment '{internal_assign_entity['title']}'.",
    #                         "weight": 3, # 数据流关系通常具有较高权重
    #                         "combined_degree": 0,
    #                         "text_unit_ids": [f"{filepath}#{self._get_text_unit_ids(assign_info)}"],
    #                     })

    #     return always_block_entity
        
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
                
    def _to_json(self,data,indent=2):
        return json.dumps(data,indent=indent,default=str)
    
    def get_kg(self):
        self._build_kg()
        return self._to_json(self.entities),self._to_json(self.relationships)

    
