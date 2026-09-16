class Solution:
    def productExceptSelf(self, nums):
        n = len(nums)
        answer = [1] * n

        # Product of elements on the left
        left = 1

        for i in range(n):
            answer[i] = left
            left *= nums[i]

        # Product of elements on the right
        right = 1

        for i in range(n - 1, -1, -1):
            answer[i] *= right
            right *= nums[i]

        return answer