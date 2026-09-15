# Definition for a binary tree node.
# class TreeNode:
#     def __init__(self, val=0, left=None, right=None):
#         self.val = val
#         self.left = left
#         self.right = right
class Solution:
    PathSum = -float("inf")
    def maxPathSum(self, root: Optional[TreeNode]) -> int:
        def sol(node):
            left, right = 0,0
            if node.left:
                left = sol(node.left)
            if node.right:
                right = sol(node.right)
            self.PathSum = max(self.PathSum, left + node.val + right)
            return max(node.val + max(left,right),0)
        sol(root)
        return(self.PathSum)
