class Solution(object):
    def maxOperations(self, nums, k):
        nums.sort()
        start=0
        end=len(nums)-1
        count=0
        while start<end:
            total=nums[start]+nums[end]
            if total==k:
                count+=1
                start+=1
                end-=1
            elif total<k:
                start+=1
            else:
                end-=1
        return count
            
