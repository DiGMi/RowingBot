class Boat(object):
    def __init__(self,size):
        self.rowers = [None]*size

    def add_rower(self, pos, name):
        self.rowers[pos-1] = name

    def get_missing(self):
        ret = []
        i = 1
        for x in self.rowers:
            if x == None:
                ret.append(i)
            i += 1
        return ret
