#!/usr/bin/env python3
"""Experiment 3.9: Kernel Circular Doubly-Linked List (list_head Model)."""

class ColorNode:
    def __init__(self, name, r, g, b):
        self.name, self.rgb = name, (r, g, b)
        self.prev = self
        self.next = self

class CircularKernelList:
    def __init__(self):
        self.head = None

    def append(self, node):
        if self.head is None:
            self.head = node
        else:
            tail = self.head.prev
            tail.next = node
            node.prev = tail
            node.next = self.head
            self.head.prev = node

    def traverse_forward(self):
        curr = self.head
        print("Forward Circular Traversal:")
        while True:
            r, g, b = curr.rgb
            print(f"  Node: {curr.name:<12} RGB=({r:3d}, {g:3d}, {b:3d})")
            curr = curr.next
            if curr is self.head:
                break

if __name__ == "__main__":
    klist = CircularKernelList()
    for item in [("Ash Slate", 75, 82, 92), ("Steel Grey", 110, 120, 134), ("Obsidian", 34, 37, 42)]:
        klist.append(ColorNode(*item))
    klist.traverse_forward()
