import random

#--------------------------------------------------------------------------
class Write:
    """ Creates slave address, rw, register address of slave, data for writing """
    def __init__(self):
        self.__addr_slv = add_zero(format(random.randrange(0, 2**7), "b"), 7);
        self.__rw_wr = "0";
        self.__addr_slv_wr = self.__addr_slv + self.__rw_wr;
        self.__addr_reg = add_zero(format((random.randrange(0, 2**8)), "b"));
        self.__data = add_zero(format((random.randrange(0, 2**8)), "b"));

    def addr_slv(self) -> str:
        return self.__addr_slv

    def rw_wr(self) -> str:
        return self.__rw_wr

    def addr_slv_wr(self) -> str:
        return self.__addr_slv_wr

    def addr_reg(self) -> str:
        return self.__addr_reg

    def data(self) -> str:
        return self.__data

    def new_data(self):
        """ Overwrite data """
        self.__data = add_zero(format((random.randrange(0, 2**8)), "b"));

    def __repr__(self):
        return (f'{self.__class__.__name__}('
                f'{self.__addr_slv!r} : addr_slv, {self.__rw_wr!r} : rw_wr, '
                f'{self.__addr_slv_wr!r} : addr_slv_wr, {self.__addr_reg!r} : addr_reg, '
                f'{self.__data!r} : data)')

#--------------------------------------------------------------------------
class Read:
    """ Creates slave address, rw, register address of slave, data from slave for reading """
    def __init__(self):
        self.__addr_slv = add_zero(format(random.randrange(0, 2**7), "b"), 7);
        self.__rw_wr = "0";
        self.__rw_rd = "1";
        self.__addr_slv_wr = self.__addr_slv + self.__rw_wr;
        self.__addr_slv_rd = self.__addr_slv + self.__rw_rd;
        self.__addr_reg = add_zero(format((random.randrange(0, 2**8)), "b"));
        self.__data_from_slv = add_zero(format((random.randrange(0, 2**8)), "b"));

    def addr_slv(self) -> str:
        return self.__addr_slv

    def rw_wr(self) -> str:
        return self.__rw_wr

    def rw_rd(self) -> str:
        return self.__rw_rd

    def addr_slv_wr(self) -> str:
        return self.__addr_slv_wr

    def addr_slv_rd(self) -> str:
        return self.__addr_slv_rd

    def addr_reg(self) -> str:
        return self.__addr_reg

    def data_from_slv(self) -> str:
        return self.__data_from_slv

    def new_data_from_slv(self):
        """ Overwrite data """
        self.__data_from_slv = add_zero(format((random.randrange(0, 2**8)), "b"));

    def __repr__(self):
        return (f'{self.__class__.__name__}('
                f'{self.__addr_slv!r} : addr_slv, {self.__rw_wr!r} : rw_wr, '
                f'{self.__rw_rd!r} : rw_rd, {self.__addr_slv_wr!r} : addr_slv_wr, '
                f'{self.__addr_slv_rd!r} : addr_slv_rd, {self.__addr_reg!r} : addr_reg, '
                f'{self.__data_from_slv!r} : data_from_slv)')

#--------------------------------------------------------------------------
def add_zero(data:str, sz:int=8) -> str:
    """ Extends data to sz bits """
    if len(data) < sz:
        data = list(data);
        string = "";
        for i in range(sz - len(data)):
           data.insert(i, "0")
        for i in data:
            string += i;
        data = string
    return data