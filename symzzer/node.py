import heapq

class Node:
    def __init__(self, seed, cbbVal, path):
        self.seeds = [seed]

        self.path = path
        self.cbbVal = cbbVal

    def __lt__(self, other):
        if self.cbbVal < other.cbbVal:
            return 0
        elif self.cbbVal == other.cbbVal:
            return 0
        else:
            return -1

class PriorityQueue(object):
    def __init__(self):
        self._queue = []

    def push(self, item):
        heapq.heappush(self._queue, item)

    def pop(self):
        return heapq.heappop(self._queue)

    def head(self):
        return self._queue[0]

    def qsize(self):
        return len(self._queue)

    def empty(self):
        return True if not self._queue else False
    

    # def getPath(self):
    #     return [cbr[0] for cbr in self.cbrs]    
    # def getCbbs(self):
    #     return [cbr[1] for cbr in self.cbrs]

    def getAllPath(self):
        return [item.path for item in self._queue]

'''
# test pqueue
if __name__ == "__main__":

    node1 = Node(1,1, [])

    node2 = Node(2,2 ,[])

    node3 = Node(3, 3, [])


    pqueue = PriorityQueue()
    pqueue.push(node1)
    pqueue.push(node3)
    pqueue.push(node2)
    kk = pqueue.pop()
    print(kk.seeds)
    pqueue.head().cbbVal = 0
    while not pqueue.empty():
        item = pqueue.pop()
        print(item.cbbVal, item.seeds)
'''