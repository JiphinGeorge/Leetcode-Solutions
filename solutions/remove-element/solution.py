class Solution(object):
    def removeElement(self, nums, val):

        k = 0

        for i in range(len(nums)):

            # Keep only elements that are not equal to val.
            if nums[i] != val:
                nums[k] = nums[i]
                k += 1

        return k