class Solution(object):
    def majorityElement(self, nums):
        """
        :type nums: List[int]
        :rtype: int
        """
        dic={}
        max_val=0
        key=0
        for i in nums:
            if i in dic:
                dic[i]+=1
            else :
                dic[i]=1
        for i in dic:
            if dic[i]>max_val:
                max_val=dic[i]
                key=i
        return key

        '''nums.sort()
        l=len(nums)
        return nums[l//2]'''



        