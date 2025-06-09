import json
import os
from collections import defaultdict 

from pyverilog.vparser.parser import parse
from pyverilog.vparser.ast import *
from pyverilog.dataflow.visit import NodeVisitor
from pyverilog.dataflow.dataflow_analyzer import VerilogDataflowAnalyzer

    # test_verilog_content = """
    #    module example_top (
    #    input clk_i,
    #    input rst_ni,
    #    output reg [7:0] data_o,
    #    input [3:0] addr_i
    #    );
    #    parameter DEFAULT_VALUE = 32'hABCD;
    #    localparam STATE_IDLE = 2'b00;

    #    wire [7:0] internal_wire;
    #    reg [7:0] counter_reg;
    #    reg [2:0] state_reg;
    #    reg [7:0] memory [0:63];
    #    assign #10 internal_wire = addr_i * 2;
    #    reg [15:0] large_mem [0:10][0:20];

    #    // **** 在这里实例化修改后的模块来测试各种情况 ****
    #    // 1. 普通实例化，带参数覆盖
    #    generic_sub_module #(
    #        .DATA_WIDTH ( 8 ) // 覆盖 DATA_WIDTH 为 8
    #    ) u_sub_module_8bit (
    #        .in_data ( clk_i ), // 假设 clk_i 作为单比特输入
    #        .out_data ( data_o[0] ) // 假设只连接一位
    #    );

    #    // 2. 普通实例化，不带参数覆盖（使用默认参数）
    #    generic_sub_module u_sub_module_default (
    #        .in_data ( clk_i ),
    #        .out_data ( data_o[1] )
    #    );

    #    // 3. 数组实例化，且带参数覆盖
    #    generic_sub_module #(
    #        .DATA_WIDTH ( 4 ) // 覆盖 DATA_WIDTH 为 4
    #    ) u_sub_module_array [0:7] ( // 实例化8个相同的模块
    #        .in_data ( addr_i ), // addr_i 是 [3:0]，刚好4位
    #        .out_data ( internal_wire[3:0] ) // 假设连接到 internal_wire 的部分
    #    );

    #    // 4. 另一个数组实例化，不带参数覆盖
    #    generic_sub_module u_sub_module_array_default [0:3] (
    #        .in_data ( addr_i[0] ),
    #        .out_data ( data_o[2] )
    #    );
    #    // **** 实例化结束 ****

    #    always @(posedge clk_i or negedge rst_ni) begin
    #        if (!rst_ni) begin
    #            counter_reg <= 8'h00;
    #        end else begin
    #            counter_reg <= counter_reg + 1;
    #        end
    #    end

    #    always_comb begin : comb_logic
    #        case(state_reg)
    #            STATE_IDLE: begin
    #                data_o = 8'h00;
    #            end
    #            default: begin
    #                data_o = 8'hFF;
    #            end
    #        endcase
    #    end

    #    endmodule



    #     // **** 修改后的 another_sub_module 定义，现在命名为 generic_sub_module ****
    #     module generic_sub_module #(
    #     parameter DATA_WIDTH = 1 // 默认数据位宽为1
    #     ) (
    #     input [DATA_WIDTH-1:0] in_data,
    #     output reg [DATA_WIDTH-1:0] out_data,
    #     input clk
    #     );

    #     wire [DATA_WIDTH-1:0] internal_signal;
    #     reg [DATA_WIDTH-1:0] reg_data;


    #     assign internal_signal = in_data;


    #     always @(posedge clk) begin
    #         reg_data <= internal_signal;
    #         out_data <= reg_data;
    #     end

    #     endmodule
    # """

    # temp_verilog_path = "./temp_design_with_all_elements.v"
    # with open(temp_verilog_path, "w",encoding='utf-8') as f:
    #     f.write(test_verilog_content)

class CollectRTLInfo:
    def __init__(self):
    # 以下类型全部存放节点类，后续统一进行处理
        self.modules = []       
        self.ports = []        
        self.signals = []       
        self.registers = [] 
        self.wires=[]    
        self.parameters = []    
        self.instances = []     
        self.assigns = []       
        self.always_blocks = [] 

        self.current_filepath=None

        self.wait_nodes = defaultdict(lambda: {
            "modules": [],
            "ports": [],
            "signals": [],
            "registers": [],
            "wires": [],
            "parameters": [],
            "instances": [],
            "assigns": [],
            "always_blocks": [],
            "initial_blocks": [],
        })
        self.parsed_data = defaultdict(lambda: {
            "modules": [],
            "ports": [],
            "signals": [],
            "registers": [],
            "wires": [],
            "parameters": [],
            "instances": [],
            "assigns": [],
            "always_blocks": [],
            "initial_blocks": [],
            "dataflow":[]
        })
        self.global_module_definitions = {}
        self.processed_files = set()
    # 将所有遇到的节点添加到列表中
    def add_module(self,node,filepath):
        self.wait_nodes[filepath]["modules"].append(node)

    def add_port(self,node,module_name,filepath):
        self.wait_nodes[filepath]["ports"].append((node,module_name))

    def add_signal(self,node,module_name,filepath):
        self.wait_nodes[filepath]["signals"].append((node,module_name))

    def add_register(self,node,module_name,filepath):
        self.wait_nodes[filepath]["registers"].append((node,module_name))

    def add_wire(self,node,module_name,filepath):
        self.wait_nodes[filepath]["wires"].append((node,module_name))

    def add_parameter(self,node,module_name,filepath):
        self.wait_nodes[filepath]["parameters"].append((node,module_name))

    def add_instance(self,node,module_name,filepath):
        self.wait_nodes[filepath]["instances"].append((node,module_name))

    def add_assign(self,node,module_name,filepath):
        self.wait_nodes[filepath]["assigns"].append((node,module_name))

    def add_always_block(self,node,module_name,filepath):
        self.wait_nodes[filepath]["always_blocks"].append((node,module_name))

    def _get_value(self,node):
        # 基本情况：如果node是字符串
        if isinstance(node, str):
            return node

        # Level 1 (Highest Priority)
        # 处理一元操作符
        elif isinstance(node, Uplus):
            right = self._get_value(node.right)
            if isinstance(node.right, Identifier):
                return f"+{right}"
            else:
                return f"+({right})"

        elif isinstance(node, Uminus):
            right = self._get_value(node.right)
            if isinstance(node.right, Identifier):
                return f"-{right}"
            else:
                return f"-({right})"

            # 处理逻辑非操作
        elif isinstance(node, Ulnot):
            right = self._get_value(node.right)
            # 对简单标识符，不需要额外括号
            if isinstance(node.right, Identifier):
                return f"!{right}"
            # 其他情况加括号以确保优先级正确
            return f"!({right})"

            # 处理按位非操作
        elif isinstance(node, Unot):
            right = self._get_value(node.right)
            # 对简单标识符，不需要额外括号
            if isinstance(node.right, Identifier):
                return f"~{right}"
            # 其他情况加括号以确保优先级正确
            return f"~({right})"

        elif isinstance(node, Uand):
            right = self._get_value(node.right)
            # 对简单标识符，不需要额外括号
            if isinstance(node.right, Identifier):
                return f"&{right}"
            # 其他情况加括号以确保优先级正确
            return f"&({right})"   

        elif isinstance(node, Unand):
            right = self._get_value(node.right)
            # 对简单标识符，不需要额外括号
            if isinstance(node.right, Identifier):
                return f"~&{right}"
            # 其他情况加括号以确保优先级正确
            return f"~&({right})" 

        elif isinstance(node, Uor):
            right = self._get_value(node.right)
            # 对简单标识符，不需要额外括号
            if isinstance(node.right, Identifier):
                return f"|{right}"
            # 其他情况加括号以确保优先级正确
            return f"|({right})"

        elif isinstance(node, Unor):
            right = self._get_value(node.right)
            # 对简单标识符，不需要额外括号
            if isinstance(node.right, Identifier):
                return f"~|{right}"
            # 其他情况加括号以确保优先级正确
            return f"~|({right})"

        elif isinstance(node, Uxor):
            right = self._get_value(node.right)
            # 对简单标识符，不需要额外括号
            if isinstance(node.right, Identifier):
                return f"^{right}"
            # 其他情况加括号以确保优先级正确
            return f"^({right})"

        elif isinstance(node, Uxnor):
            right = self._get_value(node.right)
            # 对简单标识符，不需要额外括号
            if isinstance(node.right, Identifier):
                return f"~^{right}"
            # 其他情况加括号以确保优先级正确
            return f"~^({right})"

        # Level 2
        elif isinstance(node,Power):
            left=self._get_value(node.left)
            right=self._get_value(node.right)
            return f"({left}**{right})"

        elif isinstance(node, Times):
            left = self._get_value(node.left)
            right = self._get_value(node.right)
            return f"({left} * {right})"

        elif isinstance(node, Divide):
            left = self._get_value(node.left)
            right = self._get_value(node.right)
            return f"({left} / {right})"


        elif isinstance(node, Mod):
            left = self._get_value(node.left)
            right = self._get_value(node.right)
            return f"({left} % {right})"

        # Level 3
        # 处理算术操作符
        elif isinstance(node, Plus):
            left = self._get_value(node.left)
            right = self._get_value(node.right)
            return f"({left} + {right})"

        elif isinstance(node, Minus):
            left = self._get_value(node.left)
            right = self._get_value(node.right)
            return f"({left} - {right})"

        # 处理移位操作
        elif isinstance(node, Sll):
            left = self._get_value(node.left)
            right = self._get_value(node.right)
            return f"({left} << {right})"

        elif isinstance(node, Srl):
            left = self._get_value(node.left)
            right = self._get_value(node.right)
            return f"({left} >> {right})"

        elif isinstance(node, Sla):
            left = self._get_value(node.left)
            right = self._get_value(node.right)
            return f"({left} <<< {right})"

        elif isinstance(node, Sra):
            left = self._get_value(node.left)
            right = self._get_value(node.right)
            return f"({left} >>> {right})"

        # Level 5
        # 处理比较操作符
        elif isinstance(node, LessThan):
            left = self._get_value(node.left)
            right = self._get_value(node.right)
            return f"({left} < {right})"

        elif isinstance(node, GreaterThan):
            left = self._get_value(node.left)
            right = self._get_value(node.right)
            return f"({left} > {right})"

        elif isinstance(node, LessEq):
            left = self._get_value(node.left)
            right = self._get_value(node.right)
            return f"({left} <= {right})"

        elif isinstance(node, GreaterEq):
            left = self._get_value(node.left)
            right = self._get_value(node.right)
            return f"({left} >= {right})"

        # Level 6
        # 处理相等比较
        elif isinstance(node, Eq):
            left = self._get_value(node.left)
            right = self._get_value(node.right)
            return f"({left} == {right})"

        # 处理不等比较
        elif isinstance(node, NotEq):
            left = self._get_value(node.left)
            right = self._get_value(node.right)
            return f"({left} != {right})"

            # 处理相等比较
        elif isinstance(node, Eql):
            left = self._get_value(node.left)
            right = self._get_value(node.right)
            return f"({left} === {right})"

        # 处理不等比较
        elif isinstance(node, NotEql):
            left = self._get_value(node.left)
            right = self._get_value(node.right)
            return f"({left} !== {right})"

        # Level 7
        # 处理按位与操作
        elif isinstance(node, And):
            left = self._get_value(node.left)
            right = self._get_value(node.right)
            return f"({left} & {right})"

        # 处理异或操作
        elif isinstance(node, Xor):
            left = self._get_value(node.left)
            right = self._get_value(node.right)
            return f"({left} ^ {right})"

        # 处理同或操作
        elif isinstance(node, Xnor):
            left = self._get_value(node.left)
            right = self._get_value(node.right)
            return f"({left} ~^ {right})"

        # Level 8
        # 处理按位或操作
        elif isinstance(node, Or):
            left = self._get_value(node.left)
            right = self._get_value(node.right)
            return f"({left} | {right})"

        ## Level 9
        # 处理逻辑与操作
        if isinstance(node, Land):
            left = self._get_value(node.left)
            right = self._get_value(node.right)
            return f"({left} && {right})"

        # Level 10
        # 处理逻辑或操作
        elif isinstance(node, Lor):
            left = self._get_value(node.left)
            right = self._get_value(node.right)
            return f"({left} || {right})"

        # Level 11
        elif isinstance(node,Cond):
            cond=self._get_value(node.cond)
            true_value=self._get_value(node.true_value)
            false_value=self._get_value(node.false_value)
            return f"({cond})? {true_value}:{false_value}"


        elif isinstance(node,Repeat):
            times = self._get_value(node.times)
            value = self._get_value(node.value)
            return f"{{{times}{{{value}}}}}"

        elif isinstance(node,Concat):
            parts=[self._get_value(child_node) for child_node in node.children()]
            return "{" + ", ".join(parts) + "}"

        elif isinstance(node,DelayStatement):
            return f"#{self._get_value(node.delay)}"
        # 处理部分选择 (如 signal[1:0])
        elif isinstance(node, Partselect):
            var=self._get_value(node.var)
            msb=self._get_value(node.msb)
            lsb=self._get_value(node.lsb)
            return f"{var}[{msb}:{lsb}]"
        # 处理指针访问 (如 array[index])
        elif isinstance(node, Pointer):

            var=self._get_value(node.var)
            ptr=self._get_value(node.ptr)
            return f"{var}[{ptr}]"
        # 处理标识符
        elif isinstance(node, Identifier):
            return node.name

        # 处理IntConst, 增加对数字常量的处理
        elif isinstance(node, IntConst):
            return node.value

        # 处理FloatConst
        elif isinstance(node, FloatConst):
            return node.value

        # 处理StringConst
        elif isinstance(node, StringConst):
            return f'"{node.value}"'
            
        try:
            result = str(node)
            # 清理元组表示形式，如 "(BYTE_0,)"
            result = result.replace("(", "").replace(")", "").replace(",", "")
            return result
        except:
            return "unknown_node"
########################################################################
    def _get_width(self,node_width):
        if node_width:
            msb=self._get_value(node_width.msb)
            lsb=self._get_value(node_width.lsb)
            return {'msb':msb,'lsb':lsb}
        else:
            return {'msb':0,'lsb':0}
    
    def _get_signed(self,node_signed):
        return node_signed
    
    def _get_dimensions(self,node_dimensions):
        if node_dimensions:
            dims=[]
            for d in node_dimensions.children():
                dims.append(self._get_width(d))
            return dims
        return []
    
    def _get_direction(self,node_direction):
        if isinstance(node_direction,Input):
            return "input"
        elif isinstance(node_direction,Output):
            return "output"
        elif isinstance(node_direction,Inout):
            return "inout"

    def _get_senslist(self,node_senslist):
        senslist=[]
        for sens in node_senslist.list:
            edge=sens.type
            sig=sens.sig.name
            senslist.append({"edge":edge,"sig":sig})
        return senslist
    def _find_last_line_number(self,node):
        max_line = getattr(node, 'lineno', 0)
        
        if hasattr(node, 'end_lineno') and node.end_lineno is not None:
            return node.end_lineno
        
        if hasattr(node, 'children'):
            for child in node.children():
                child_last_line = self._find_last_line_number(child)
                if child_last_line and child_last_line > max_line:
                    max_line = child_last_line
        
        return max_line

    def _get_ast(self,node_type):
        return str(type(node_type)).split(".")[-1].replace("'>","")

    def _get_dataflow(self,filepath,module):
        analyzer = VerilogDataflowAnalyzer(filepath,module)
        analyzer.generate()
        binddict = analyzer.getBinddict()
        ret=[]
        for bk, bv in sorted(binddict.items(), key=lambda x: str(x[0])):
            for bvi in bv:
                ret.append(bvi.tostr())
        return ret
    
    def _determine_logic_type(self,always_node):
        if not hasattr(always_node, 'sens_list'):
            return 'combinational'
        
        sens_list = always_node.sens_list
        
        if isinstance(sens_list, SensList):
            sensitivity_items = sens_list.list    
            if len(sensitivity_items) == 1 and str(sensitivity_items[0]) == '*':
                return 'combinational'
            
            for sens_item in sensitivity_items:
                if isinstance(sens_item, Sens):
                    if hasattr(sens_item, 'type'):
                        sens_type = sens_item.type
                        
                        if sens_type in ('posedge', 'negedge'):
                            return 'sequential'
                
                sens_str = str(sens_item).strip()
                if 'posedge' in sens_str or 'negedge' in sens_str:
                    return 'sequential'
        return 'combinational'
    
    def _collect_structured_variable_paths(self,node, conditions=None, variable_paths=None, logic_type=None, in_always=False, current_scope="", code_blocks=None, current_block_id=None):
        if conditions is None:
            conditions = []
        if variable_paths is None:
            variable_paths = {}
        if code_blocks is None:
            code_blocks = {}
        
        line_number = getattr(node, 'lineno', None)

                
        if isinstance(node, Always):
            in_always = True
            start_line = line_number
            end_line = self._find_last_line_number(node)
            
            block_id = f"id_{len(code_blocks) + 1}"
            
            current_logic_type = self._determine_logic_type(node)
            logic_type = current_logic_type
            
            code_blocks[block_id] = {
                "type": "AlwaysBlock",
                "start_line": start_line,
                "end_line": end_line,
                "logic_type": current_logic_type,
                "description": f"Always block starting at line {start_line}",
                "variable_assignments": {}
            }
            

            self._collect_structured_variable_paths(node.statement, conditions, variable_paths, logic_type, in_always, current_scope, code_blocks, block_id)
        
        elif isinstance(node, IfStatement):
            cond_str = self._get_value(node.cond)
            true_cond = conditions + [cond_str]

            self._collect_structured_variable_paths(node.true_statement, true_cond, variable_paths, logic_type, in_always, current_scope, code_blocks, current_block_id)
            
            if node.false_statement:
                false_cond = conditions + [f"!({cond_str})"]
                self._collect_structured_variable_paths(node.false_statement, false_cond, variable_paths, logic_type, in_always, current_scope, code_blocks, current_block_id)
                
        elif isinstance(node, CaseStatement):
            case_expr = self._get_value(node.comp)
            handled_conditions = []
            
            # Process each case branch
            for case in node.caselist:
                if case.cond is not None:
                    # Normal case branch
                    if isinstance(case.cond, list):
                        case_conditions = []
                        for cond_item in case.cond:
                            formatted_item = self._get_value(cond_item)
                            case_condition = f"{case_expr} == {formatted_item}"
                            case_conditions.append(case_condition)
                            handled_conditions.append(case_condition)
                        
                        combined_condition = " || ".join(case_conditions)
                        
                        self._collect_structured_variable_paths(case.statement, conditions + [f"({combined_condition})"], 
                                                variable_paths, logic_type, in_always, current_scope, code_blocks, current_block_id)
                    else:
                        formatted_cond = self._get_value(case.cond)
                        formatted_cond = formatted_cond.replace("(", "").replace(")", "").replace(",", "")
                        case_condition = f"{case_expr} == {formatted_cond}"
                        handled_conditions.append(case_condition)
                        
                        self._collect_structured_variable_paths(case.statement, conditions + [case_condition], 
                                                variable_paths, logic_type, in_always, current_scope, code_blocks, current_block_id)
                else:
                    is_default = True
                    
                    if is_default:
                        if handled_conditions:
                            not_conditions = [f"!({cond})" for cond in handled_conditions]
                            default_condition = " && ".join(not_conditions)
                            
                            self._collect_structured_variable_paths(case.statement, conditions + [f"({default_condition})"], 
                                            variable_paths, logic_type, in_always, current_scope, code_blocks, current_block_id)
                        else:
                            default_condition = f"default({case_expr})"
                            
                            self._collect_structured_variable_paths(case.statement, conditions + [default_condition], 
                                            variable_paths, logic_type, in_always, current_scope, code_blocks, current_block_id)
                    else:
                        self._collect_structured_variable_paths(case.statement, conditions, 
                                            variable_paths, logic_type, in_always, current_scope, code_blocks, current_block_id)
        
        elif isinstance(node, (BlockingSubstitution, NonblockingSubstitution)):
            left_var=self._get_value(node.left.var)
            right_expr=self._get_value(node.right.var)
            assignment_type = 'non-blocking' if isinstance(node, NonblockingSubstitution) else 'blocking'
            current_logic_type = logic_type if in_always else 'combinational'
            
            if current_scope and left_var:
                scoped_var = f"{current_scope}.{left_var}"
            else:
                scoped_var = left_var
            
            if left_var:
                if conditions:
                    formatted_conditions = conditions
                    condition_str = ' && '.join(formatted_conditions)
                else:
                    condition_str = "always"
                
                assignment_info = {
                    "condition": condition_str,
                    "line": line_number,
                    "logic_type": current_logic_type,
                    "assignment_type": assignment_type,
                    "right_expr": right_expr
                }
                
                if current_block_id and current_block_id in code_blocks:
                    if scoped_var not in code_blocks[current_block_id]["variable_assignments"]:
                        code_blocks[current_block_id]["variable_assignments"][scoped_var] = []
                    code_blocks[current_block_id]["variable_assignments"][scoped_var].append(assignment_info)
                
                if scoped_var not in variable_paths:
                    variable_paths[scoped_var] = []
                variable_paths[scoped_var].append((condition_str, line_number, current_logic_type, assignment_type, right_expr))
        
        elif isinstance(node, Assign):
            left_var=self._get_value(node.left.var)
            right_expr=self._get_value(node.right.var)
            
            if current_scope and left_var:
                scoped_var = f"{current_scope}.{left_var}"
            else:
                scoped_var = left_var
            
            if left_var:
                block_id = f"id_{len(code_blocks) + 1}"
                
                code_blocks[block_id] = {
                    "type": "AssignBlock",
                    "start_line": line_number,
                    "end_line": line_number,
                    "logic_type": "combinational",
                    "description": f"Assign statement at line {line_number}",
                    "variable_assignments": {}
                }
                
                assignment_info = {
                    "condition": "None",
                    "line": line_number,
                    "logic_type": "combinational",
                    "assignment_type": "continuous",
                    "right_expr": right_expr
                }
                
                code_blocks[block_id]["variable_assignments"][scoped_var] = [assignment_info]
                
                if scoped_var not in variable_paths:
                    variable_paths[scoped_var] = []
                variable_paths[scoped_var].append(("None", line_number, "combinational", "continuous", right_expr))

        elif hasattr(node, 'children'):
            for child in node.children():
                self._collect_structured_variable_paths(child, conditions, variable_paths, logic_type, in_always, current_scope, code_blocks, current_block_id)
        
        return variable_paths, code_blocks

#######################################################################

    def parse_node(self,filepath=None,type=None):
        #未指定具体路径，则全部解析
        if filepath is None:
            for path in self.wait_nodes.keys():
                if type is None:
                    for current_type in self.wait_nodes[path].keys():
                        method_name=f"_parse_{current_type}"
                        if hasattr(self, method_name) and callable(getattr(self, method_name)):
                            print(f"Attempting to call {method_name} for {path}")
                            method_to_call = getattr(self, method_name)
                            method_to_call(path)
                        else:
                            print(f"Warning: No parsing method found for type '{current_type}' ({method_name}) in file {path}")
                else:
                    current_type=type
                    method_name=f"_parse_{current_type}"
                    if hasattr(self, method_name) and callable(getattr(self, method_name)):
                        print(f"Attempting to call {method_name} for {path}")
                        method_to_call = getattr(self, method_name)
                        method_to_call(path)
                    else:
                        print(f"Warning: No parsing method found for type '{current_type}' ({method_name}) in file {path}")

        else:
            path=filepath
            if type is None:
                for current_type in self.wait_nodes[path].keys():
                    method_name=f"_parse_{current_type}"
                    if hasattr(self, method_name) and callable(getattr(self, method_name)):
                        print(f"Attempting to call {method_name} for {path}")
                        # 使用 getattr 动态获取方法并调用
                        method_to_call = getattr(self, method_name)
                        method_to_call(path)
                    else:
                        print(f"Warning: No parsing method found for type '{current_type}' ({method_name}) in file {path}")
            else:
                current_type=type
                method_name=f"_parse_{current_type}"
                if hasattr(self, method_name) and callable(getattr(self, method_name)):
                    print(f"Attempting to call {method_name} for {path}")
                    method_to_call = getattr(self, method_name)
                    method_to_call(path)
                else:
                    print(f"Warning: No parsing method found for type '{current_type}' ({method_name}) in file {path}")            
        return self._to_json()
    
    def _parse_modules(self,filepath):
        for module in self.wait_nodes[filepath]["modules"]:
            self.parsed_data[filepath]["modules"].append({
                "name":module.name,
                "lineno":module.lineno,
                "ast":self._get_ast(module),
                "startline":module.lineno,
                "endline":module.lineno
            })

    def _parse_ports(self,filepath):
        for node,module_name in self.wait_nodes[filepath]["ports"]:
            self.parsed_data[filepath]["ports"].append({
                "name":node.name,
                "lineno":node.lineno,
                "direction":self._get_direction(node),
                "msb":self._get_width(node.width)["msb"],
                "lsb":self._get_width(node.width)["lsb"],
                "signed":self._get_signed(node.signed),
                "dimensions":self._get_dimensions(node.dimensions),
                "value":self._get_value(node.value),
                "ast":self._get_ast(node),
                "startline":node.lineno,
                "endline":self._find_last_line_number(node),
                "parent_module":module_name
            })

    def _parse_registers(self,filepath):
        for node ,module_name in self.wait_nodes[filepath]["registers"]:
            self.parsed_data[filepath]["registers"].append({
                "name":node.name,
                "lineno":node.lineno,
                "msb":self._get_width(node.width)["msb"],
                "lsb":self._get_width(node.width)["lsb"],
                "signed":self._get_signed(node.signed),
                "dimensions":self._get_dimensions(node.dimensions),
                "value":self._get_value(node.value),
                "ast":self._get_ast(node),
                "startline":node.lineno,
                "endline":self._find_last_line_number(node),
                "parent_module":module_name
            })

    def _parse_parameters(self,filepath):
        for node,module_name in self.wait_nodes[filepath]["parameters"]:
            self.parsed_data[filepath]["parameters"].append({
                "name":node.name,
                "lineno":node.lineno,
                "msb":self._get_width(node.width)["msb"],
                "lsb":self._get_width(node.width)["lsb"],
                "signed":self._get_signed(node.signed),
                "dimensions":self._get_dimensions(node.dimensions),
                "value":self._get_value(node.value.var),
                "ast":self._get_ast(node),
                "startline":node.lineno,
                "endline":self._find_last_line_number(node),
                "parent_module":module_name
            })

    def _parse_wires(self,filepath):
        for node ,module_name in self.wait_nodes[filepath]["wires"]:
            self.parsed_data[filepath]["wires"].append({
                "name":node.name,
                "lineno":node.lineno,
                "msb":self._get_width(node.width)["msb"],
                "lsb":self._get_width(node.width)["lsb"],
                "signed":self._get_signed(node.signed),
                "dimensions":self._get_dimensions(node.dimensions),
                "value":self._get_value(node.value),
                "ast":self._get_ast(node),
                "startline":node.lineno,
                "endline":self._find_last_line_number(node),
                "parent_module":module_name
            })

    def _parse_assigns(self,filepath):
        for node,module_name in self.wait_nodes[filepath]["assigns"]:
            self.parsed_data[filepath]["assigns"].append({
                "lineno":node.lineno,
                "left":self._get_value(node.left.var),
                "right":self._get_value(node.right.var),
                "ldelay":self._get_value(node.ldelay),
                "rdelay":self._get_value(node.rdelay),
                "ast":self._get_ast(node),
                "startline":node.lineno,
                "endline":self._find_last_line_number(node),
                "parent_module":module_name,
            })

    # def parse_signals(self):
    #     """
    #     将解析后的 ports, registers, wires 数据汇总到 signals 列表中。
    #     每个信号都会被添加一个 'category' 字段以标识其原始类型。
    #     """
    #     self.parsed_data["signals"] = [] 
    #     # 遍历 ports 列表，将每个端口添加到 signals
    #     for port_info in self.parsed_data["ports"]:
    #         signal_entry = port_info.copy() # 复制一份，避免修改原始 port_info
    #         signal_entry['category'] = 'port'
    #         self.parsed_data["signals"].append(signal_entry)

    #     for reg_info in self.parsed_data["registers"]:
    #         signal_entry = reg_info.copy()
    #         signal_entry['category'] = 'register'
    #         self.parsed_data["signals"].append(signal_entry)

    #     for wire_info in self.parsed_data["wires"]:
    #         signal_entry = wire_info.copy()
    #         signal_entry['category'] = 'wire'
    #         self.parsed_data["signals"].append(signal_entry)

    def _parse_instances(self,filepath):
        for node,module_name in self.wait_nodes[filepath]["instances"]:
            ports_args=[]
            for port in node.portlist:
                ports_args.append({"portname":self._get_value(port.portname),"argname":self._get_value(port.argname)})
            parameters=[]
            for param in node.parameterlist:
                parameters.append({"paramname":param.paramname,"argname":param.argname})
            self.parsed_data[filepath]["instances"].append({
                "lineno":node.lineno,
                "module_name":node.module,
                "instance_name":node.name,
                "port_connections":ports_args,
                "parameter_connections":parameters,
                "arrays":self._get_width(node.array),
                "ast":self._get_ast(node),
                "startline":node.lineno,
                "endline":self._find_last_line_number(node),
                "parent_module":module_name
            })

    def _parse_always_blocks(self,filepath):
        for node,module_name in self.wait_nodes[filepath]["always_blocks"]:
            variable_paths,code_blocks=self._collect_structured_variable_paths(node)
            self.parsed_data[filepath]["always_blocks"].append({
                "lineno":node.lineno,
                "senlist":self._get_senslist(node.sens_list),
                "ast":self._get_ast(node),
                "startline":node.lineno,
                "endline":self._find_last_line_number(node),
                "logic_type":self._determine_logic_type(node),
                "cfg_data":code_blocks["id_1"]["variable_assignments"],
                "parent_module":module_name,
            })
    def _to_json(self,indent=2):
        return  json.dumps(self.parsed_data,indent=indent,default=str) 
    
    
class RTLCollectorVisitor(NodeVisitor):
    def __init__(self, file_path=None):
        self.collected_info = CollectRTLInfo()
        self.current_module_name = None # 用于跟踪当前正在访问的模块
        self.current_filepath=None

    def set_filepath(self,file_path):
        self.current_filepath=file_path

    def visit_ModuleDef(self,node):
        self.current_module_name=node.name
        self.collected_info.add_module(node,self.current_filepath)
        self.generic_visit(node) # 确保遍历模块内部的所有子节点
        self.current_module_name = None # 模块遍历结束后重置
    
    #遍历它们的儿子
    def visit_Paramlist(self,node):
        self.generic_visit(node)
        
    def visit_PortList(self,node):
        self.generic_visit(node)
    # def visit_Port(self,node):
    #     print(type(node))
    #     self.generic_visit(node)
# 针对 Input, Output, Inout 节点进行收集
    def visit_Input(self, node):
        self.collected_info.add_port(node,self.current_module_name,self.current_filepath)
        self.collected_info.add_signal(node,self.current_module_name,self.current_filepath) # 输入端口也是一种信号

    def visit_Output(self, node):
        self.collected_info.add_port(node,self.current_module_name,self.current_filepath)
        self.collected_info.add_signal(node,self.current_module_name,self.current_filepath) # 输出端口也是一种信号

    def visit_Inout(self, node):
        self.collected_info.add_port(node,self.current_module_name,self.current_filepath)
        self.collected_info.add_signal(node,self.current_module_name,self.current_filepath) # 双向端口也是一种信号

    def visit_Wire(self,node):
        self.collected_info.add_wire(node,self.current_module_name,self.current_filepath)
        self.collected_info.add_signal(node,self.current_module_name,self.current_filepath)

    def visit_Reg(self,node):
        self.collected_info.add_register(node,self.current_module_name,self.current_filepath)
        self.collected_info.add_signal(node,self.current_module_name,self.current_filepath)

    def visit_Parameter(self,node):
        self.collected_info.add_parameter(node,self.current_module_name,self.current_filepath)

    def visit_InstanceList(self,node):
        self.generic_visit(node)

    def visit_Instance(self,node):
        self.collected_info.add_instance(node,self.current_module_name,self.current_filepath)
    
    def visit_Assign(self,node):
        self.collected_info.add_assign(node,self.current_module_name,self.current_filepath)
    
    def visit_Always(self,node):
        self.collected_info.add_always_block(node,self.current_module_name,self.current_filepath)


def process_line(line, in_block_comment):
    """
    处理单行代码，去除注释并返回有效代码部分及块注释状态。
    """
    effective = []
    i = 0
    n = len(line)
    while i < n:
        if in_block_comment:
            # 在块注释中，查找结束符*/
            if line[i] == '*' and i + 1 < n and line[i+1] == '/':
                in_block_comment = False
                i += 2  # 跳过*/两个字符
            else:
                i += 1
        else:
            # 不在块注释中，检查注释起始符
            if line[i] == '/' and i + 1 < n:
                if line[i+1] == '/':
                    # 单行注释，跳过剩余部分
                    break
                elif line[i+1] == '*':
                    # 进入块注释
                    in_block_comment = True
                    i += 2  # 跳过/*两个字符
                else:
                    # 普通/字符（如除法运算）
                    effective.append(line[i])
                    i += 1
            else:
                # 普通字符
                effective.append(line[i])
                i += 1
    # 拼接有效代码并去除行尾空白
    effective_line = ''.join(effective).rstrip()
    return effective_line, in_block_comment

def remove_comments(input_path, output_path):
    """
    读取输入文件，删除注释和空行，写入输出文件。
    """
    in_block_comment = False
    with open(input_path, 'r',encoding='utf-8') as infile, open(output_path, 'w',encoding='utf-8') as outfile:
        for line in infile:
            effective_line, in_block_comment = process_line(line, in_block_comment)
            if effective_line:
                outfile.write(effective_line + '\n')

if __name__ == "__main__":

    vistor= RTLCollectorVisitor()
    # in_file_list=[
    #     'C:\\Users\\huijie\\Desktop\\graphrag\\svtest\\rtl\\apb.v','C:\\Users\\huijie\\Desktop\\graphrag\\svtest\\rtl\\fifo.v','C:\\Users\\huijie\\Desktop\\graphrag\\svtest\\rtl\\i2c.v'
    #     ]
    # out_file_list=[
    #     'C:\\Users\\huijie\\Desktop\\graphrag\\svtest\\pre_rtl\\apb.v','C:\\Users\\huijie\\Desktop\\graphrag\\svtest\\pre_rtl\\fifo.v','C:\\Users\\huijie\\Desktop\\graphrag\\svtest\\pre_rtl\\i2c.v'
    # ]
    in_file_list=[
        'C:\\Users\\huijie\\Desktop\\graphrag\\svtest\\rtl\\apb.v'
        ]
    out_file_list=[
        'C:\\Users\\huijie\\Desktop\\graphrag\\svtest\\pre_rtl\\apb.v'
    ]
    for inf,ouf in zip(in_file_list,out_file_list):
        remove_comments(inf,ouf) 
        #得到该文件的语法树
        ast,_=parse([str(ouf)])
        # ast.show()
        #收集该语法树信息
        vistor.set_filepath(ouf)
        vistor.visit(ast)
        break
    static_dir='C:\\Users\\huijie\\Desktop\\graphrag\\svtest\\static'
    os.makedirs(static_dir,exist_ok=True)
    with open(f'{static_dir}/data.json','w',encoding='utf-8') as f:
        f.write(vistor.collected_info.parse_node(filepath='C:\\Users\\huijie\\Desktop\\graphrag\\svtest\\pre_rtl\\apb.v'))
    
    from KGBuilder import KGBuilder
    kg=KGBuilder(vistor.collected_info)
    entities,relationships=kg.get_kg()
    kg_dir='C:\\Users\\huijie\\Desktop\\graphrag\\svtest\\kg'
    os.makedirs(kg_dir,exist_ok=True)
    with open(f'{kg_dir}/entities.json','w',encoding='utf-8') as f:
        f.write(entities)
    with open(f'{kg_dir}/relationships.json','w',encoding='utf-8') as f:
        f.write(relationships)

