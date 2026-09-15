# Definition for singly-linked list.
# class ListNode:
#     def __init__(self, x):
#         self.val = x
#         self.next = None

class Solution:
    def hasCycle(self, head: Optional[ListNode]) -> bool:
        if not head:
            return False
        i = head
        j = head
        while i and j:
            if not i.next or not j.next:
                return False 
            i = i.next
            j = j.next.next
            if i == j:
                return True
        return False
            