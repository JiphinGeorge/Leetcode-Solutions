class Solution(object):
    def maxSubArray(self, nums):
        """
        :type nums: List[int]
        :rtype: int
        """
        maxum=nums[0]
        current_sum=nums[0]
        for i in nums[1:]:
            current_sum=max(i,current_sum+i)
            maxum=max(maxum,current_sum)
        return maxum