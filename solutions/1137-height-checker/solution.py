class Solution(object):
    def heightChecker(self, heights):
        """
        :type heights: List[int]
        :rtype: int
        """
        count=0
        sor=sorted(heights)
        for i in range(len(heights)):
            if heights[i]!=sor[i]:
                count+=1
        return count
        