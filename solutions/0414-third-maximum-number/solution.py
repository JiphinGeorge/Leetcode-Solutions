class Solution(object):
    def thirdMax(self, nums):
        
        dis=list(set(nums))
        dis.sort(reverse=True)
        if len(dis)>=3:
            return dis[2]
        else:
            return dis[0]
