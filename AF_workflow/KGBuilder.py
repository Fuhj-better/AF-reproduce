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
    def _build_module(self,module_parsed_data):
        '''
        module_parsed_data:传入的是单个路径下的模块数据
        '''
        for module in module_parsed_data:
            module_entity={
                "id":str(uuid.uuid4()),
                "human_readable_id":self._get_human_readable_id(),
                "title":module["name"],
                "type":"MODULE",
                "description":"unknown",
                "text_unit_ids":"unknown",
                "frequency":1,
                "degree":0,
                "x":0,
                "y":0,
            }
            self.entities.append(module_entity)
        
    def _build_port(self,port_parsed_data):
        for port in port_parsed_data:
            port_entity={
                "id":str(uuid.uuid4()),
                "human_readable_id":self._get_human_readable_id(),
                "title":port["name"],
                "type":"MODULE",
                "description":"unknown",
                "text_unit_ids":"unknown",
                "frequency":1,
                "degree":0,
                "x":0,
                "y":0,
            }
            self.entities.append(port_entity)
    def _build_signal(self,signal_parsed_data):
        for signal in signal_parsed_data:
            signal_entity={
                "id":str(uuid.uuid4()),
                "human_readable_id":self._get_human_readable_id(),
                "title":signal["name"],
                "type":"MODULE",
                "description":"unknown",
                "text_unit_ids":"unknown",
                "frequency":1,
                "degree":0,
                "x":0,
                "y":0,
            }
            self.entities.append(signal_entity)
    def _build_instance(self,instance_parsed_data):
        for signal in instance_parsed_data:
            port_entity={
                "id":str(uuid.uuid4()),
                "human_readable_id":self._get_human_readable_id(),
                "title":signal["name"],
                "type":"MODULE",
                "description":"unknown",
                "text_unit_ids":"unknown",
                "frequency":1,
                "degree":0,
                "x":0,
                "y":0,
            }
    def _build_assign(self,assign_parsed_data):
        for assign in assign_parsed_data:
            port_entity={
                "id":str(uuid.uuid4()),
                "human_readable_id":self._get_human_readable_id(),
                "title":assign["name"],
                "type":"MODULE",
                "description":"unknown",
                "text_unit_ids":"unknown",
                "frequency":1,
                "degree":0,
                "x":0,
                "y":0,
            }
    def _build_dataflow(self,dataflow):
        for d in dataflow:
            d_entity={
                "id":str(uuid.uuid4()),
                "human_readable_id":self._get_human_readable_id(),
                "title":d["name"],
                "type":"MODULE",
                "description":"unknown",
                "text_unit_ids":"unknown",
                "frequency":1,
                "degree":0,
                "x":0,
                "y":0,
            }
    def _build_entity(self):
        pass
