class Hole:
    def __init__(self,starting_address:int,size:int):
        self.starting_address=starting_address
        self.size=size
    def __repr__(self):
        return f"Hole(start={self.starting_address}, size={self.size})"
    
class Segment:
    def __init__(self,name:str,size:int):
        self.name=name
        self.size=size
        self.allocated_address=None
        
    def is_allocated(self):
        return self.allocated_address is not None
    
    def __repr__(self):
        return f"Segment('{self.name}', size={self.size}, allocated_at={self.allocated_address})"
    
class Process:
    def __init__(self,process_id:int):
        self.process_id=process_id
        self.segments=[]
        
    def __repr__(self):
        return f"Process(id='{self.process_id}', segments={self.segments})"
    