import json
import uuid


class KGBuilder:
    def __init__(self,rtl_info):
        self.entities=[]
        self.next_id=0
        self.rtl_info=rtl_info
    def _get_human_readable_id(self):
        ret=self.next_id
        self.next_id+=1
        return ret
    
    def _get_text_unit_ids(self,type_parsed_data):
        return f"{type_parsed_data['startline']}:{type_parsed_data['endline']}"
    def _build_module(self):
        '''
        module_parsed_data:传入的是单个路径下的模块数据
        '''
        for filepath in self.rtl_info.parsed_data.keys():
            for module in self.rtl_info.parsed_data[filepath]["modules"]:
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
        
    def _build_port(self):
        for filepath in self.rtl_info.parsed_data.keys():
            for port in self.rtl_info.parsed_data[filepath]["ports"]:
                port_entity={
                    "id":str(uuid.uuid4()),
                    "human_readable_id":self._get_human_readable_id(),
                    "title":port["name"],
                    "type":"PORT",
                    "description":f"Verilog port {port['name']} is defined in {port['parent_module']} in file {filepath} from line {port['startline']} to line {port['endline']}. The direction is {port['direction']},the most significant bit is {port['msb']},the least significant bit is {port['lsb']},the dimensions is {port['dimensions']} and the ast node type is {port['ast']}.",
                    "text_unit_ids":f"{filepath}:{self._get_text_unit_ids(port)}",
                    "frequency":1,
                    "degree":0,
                    "x":0,
                    "y":0,
                }
                self.entities.append(port_entity)
    def _build_wire(self):
        for filepath in self.rtl_info.parsed_data.keys():
            for wire in self.rtl_info.parsed_data[filepath]["wires"]:
                wire_entity={
                    "id":str(uuid.uuid4()),
                    "human_readable_id":self._get_human_readable_id(),
                    "title":wire["name"],
                    "type":"WIRE",
                    "description":f"Verilog wire {wire['name']} is defined in {wire['parent_module']} in file {filepath} from line {wire['startline']} to line {wire['endline']}.The most significant bit is {wire['msb']},the least significant bit is {wire['lsb']},the dimensions is {wire['dimensions']},the value is {wire['value']} and the ast node type is {wire['ast']}.",
                    "text_unit_ids":f"{filepath}:{self._get_text_unit_ids(wire)}",
                    "frequency":1,
                    "degree":0,
                    "x":0,
                    "y":0,
                }
                self.entities.append(wire_entity)

    def _build_register(self):
        for filepath in self.rtl_info.parsed_data.keys():
            for register in self.rtl_info.parsed_data[filepath]["registers"]:
                register_entity={
                    "id":str(uuid.uuid4()),
                    "human_readable_id":self._get_human_readable_id(),
                    "title":register["name"],
                    "type":"REGISTER",
                    "description":f"Verilog register {register['name']} is defined in {register['parent_module']} in file {filepath} from line {register['startline']} to line {register['endline']}.The most significant bit is {register['msb']},the least significant bit is {register['lsb']},the dimensions is {register['dimensions']},the value is {register['value']} and the ast node type is {register['ast']}.",
                    "text_unit_ids":f"{filepath}:{self._get_text_unit_ids(register)}",
                    "frequency":1,
                    "degree":0,
                    "x":0,
                    "y":0,
                }
                self.entities.append(register_entity)

    def _build_instance(self):
        for filepath in self.rtl_info.parsed_data.keys():
            for instance in self.rtl_info.parsed_data[filepath]["instances"]:
                instance_entity={
                    "id":str(uuid.uuid4()),
                    "human_readable_id":self._get_human_readable_id(),
                    "title":f"{instance['module_name']}:{instance['instance_name']}",
                    "type":"INSTANCE",
                    "description":f"The instance name is {instance['instance_name']} and the module name is {instance['module_name']}.Defined in {instance['parent_module']} in file {filepath} from line {instance['startline']} to line {instance['endline']} and the ast node type is {instance['ast']}.Port connections:{instance['port_connections']}.Parameter overrides:{instance['parameter_connections']}.Instance array:{instance['arrays']}",
                    "text_unit_ids":f"{filepath}:{self._get_text_unit_ids(instance)}",
                    "frequency":1,
                    "degree":0,
                    "x":0,
                    "y":0,
                }
                self.entities.append(instance_entity)
    def _build_assign(self):
        for filepath in self.rtl_info.parsed_data.keys():
            for assign in self.rtl_info.parsed_data[filepath]["assigns"]:
                assign_entity={
                    "id":str(uuid.uuid4()),
                    "human_readable_id":self._get_human_readable_id(),
                    "title":assign["left"],
                    "type":"ASSIGN",
                    "description":f"The assign sentense is defined in {assign['parent_module']} in file {filepath} from line {assign['startline']} to line {assign['endline']} and the ast node type is {assign['ast']}.The left hand side is {assign['left']} and the right hand side is {assign['right']}.The left hand delay is {assign['ldelay']} and the right hand delay is {assign['rdelay']}",
                    "text_unit_ids":f"{filepath}:{self._get_text_unit_ids(assign)}",
                    "frequency":1,
                    "degree":0,
                    "x":0,
                    "y":0,
                }
                self.entities.append(assign_entity)
    # def _build_always_block(self,dataflow):
    #     for filepath in self.rtl_info.parsed_data.keys():
    #         for always_block in self.rtl_info.parsed_data[filepath]["always_blocks"]:
    #             always_block_entity={
    #                 "id":str(uuid.uuid4()),
    #                 "human_readable_id":self._get_human_readable_id(),
    #                 "title":always_block["name"],
    #                 "type":"ASSIGN",
    #                 "description":f"The assign sentense is defined in {assign['parent_module']} in file {filepath} from {assign['startline']} to {assign['endline']} and the ast node type is {assign['ast']}.The left hand side is {assign['left']} and the right hand side is {assign['right']}.The left hand delay is {assign['ldelay']} and the right hand delay is {assign['rdelay']}",
    #                 "text_unit_ids":f"{filepath}:{self._get_text_unit_ids(assign)}",
    #                 "frequency":1,
    #                 "degree":0,
    #                 "x":0,
    #                 "y":0,
    #             }
    #             self.entities.append(assign_entity)

    # def _build_cfg_data(self,dataflow):
    #     for filepath in self.rtl_info.parsed_data.keys():
    #         for always_block in self.rtl_info.parsed_data[filepath]["always_blocks"]:
    #             cfg_data_entity={
    #                 "id":str(uuid.uuid4()),
    #                 "human_readable_id":self._get_human_readable_id(),
    #                 "title":always_block["name"],
    #                 "type":"CFG",
    #                 "description":f"The assign sentense is defined in {assign['parent_module']} in file {filepath} from {assign['startline']} to {assign['endline']} and the ast node type is {assign['ast']}.The left hand side is {assign['left']} and the right hand side is {assign['right']}.The left hand delay is {assign['ldelay']} and the right hand delay is {assign['rdelay']}",
    #                 "text_unit_ids":f"{filepath}:{self._get_text_unit_ids(assign)}",
    #                 "frequency":1,
    #                 "degree":0,
    #                 "x":0,
    #                 "y":0,
    #             }
    #             self.entities.append(assign_entity)
    def _build_entity(self):
        self._build_module()
        self._build_port()
        self._build_wire()
        self._build_register()
        self._build_instance()
        self._build_assign()


    def _to_json(self,indent=2):
        return  json.dumps(self.entities,indent=indent,default=str)
    
    def get_entities(self):
        self._build_entity()
        return self._to_json()
    
