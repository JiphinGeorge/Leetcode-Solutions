class Solution(object):
    def numIdenticalPairs(self, nums):
        count = 0
        visited = {}

        for num in nums:
            if num in visited:
                count += visited[num]

            if num in visited:
                visited[num] = visited[num] + 1
            else:
                visited[num] = 1

        return count