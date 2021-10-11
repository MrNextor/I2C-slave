import random

#--------------------------------------------------------------------------  
class Write:
    def __init__(self):
        self.__addr_slv = add_zero(format(random.randrange(0, 2**7), "b"), 7);
        self.__rw_wr = "0";
        self.__addr_slv_wr = self.__addr_slv + self.__rw_wr;
        self.__addr_reg = add_zero(format((random.randrange(0, 2**8)), "b"), 8);
        self.__data = add_zero(format((random.randrange(0, 2**8)), "b"), 8);
        
    def addr_slv(self):
        return self.__addr_slv
        
    def rw_wr(self):
        return self.__rw_wr
        
    def addr_slv_wr(self):
        return self.__addr_slv_wr
        
    def addr_reg(self):
        return self.__addr_reg
        
    def data(self):
        return self.__data

    def new_data(self):
        self.__data = add_zero(format((random.randrange(0, 2**8)), "b"), 8);

#-------------------------------------------------------------------------- 
class Read:
    def __init__(self):
        self.__addr_slv = add_zero(format(random.randrange(0, 2**7), "b"), 7);
        self.__rw_wr = "0";
        self.__rw_rd = "1";
        self.__addr_slv_wr = self.__addr_slv + self.__rw_wr;
        self.__addr_slv_rd = self.__addr_slv + self.__rw_rd;
        self.__addr_reg = add_zero(format((random.randrange(0, 2**8)), "b"), 8);
        self.__data_from_slv = add_zero(format((random.randrange(0, 2**8)), "b"), 8);

    def addr_slv(self):
        return self.__addr_slv
        
    def rw_wr(self):
        return self.__rw_wr

    def rw_rd(self):
        return self.__rw_rd

    def addr_slv_wr(self):
        return self.__addr_slv_wr
        
    def addr_slv_rd(self):
        return self.__addr_slv_rd
    
    def addr_reg(self):
        return self.__addr_reg
        
    def data_from_slv(self):
        return self.__data_from_slv    
    
    def new_data_from_slv(self):
        self.__data_from_slv = add_zero(format((random.randrange(0, 2**8)), "b"), 8);

#--------------------------------------------------------------------------      
def add_zero(data, sz):    
    if len(data) < sz:
        need = sz - len(data);
        data = list(data);
        for i in range(need):
           data.insert(i, "0")
        string = "";
        for i in data:
            string += i;
        data = string
    return data    