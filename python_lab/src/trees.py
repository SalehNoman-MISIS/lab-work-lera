from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass
class BSTNode:
    key: int
    left: Optional["BSTNode"] = None
    right: Optional["BSTNode"] = None


class BinarySearchTree:
    """Simple unbalanced binary search tree with unique keys."""

    def __init__(self) -> None:
        self.root: Optional[BSTNode] = None
        self.size = 0

    def insert(self, key: int) -> None:
        if self.root is None:
            self.root = BSTNode(key)
            self.size += 1
            return

        current = self.root
        while current is not None:
            if key < current.key:
                if current.left is None:
                    current.left = BSTNode(key)
                    self.size += 1
                    return
                current = current.left
            elif key > current.key:
                if current.right is None:
                    current.right = BSTNode(key)
                    self.size += 1
                    return
                current = current.right
            else:
                return

    def search(self, key: int) -> bool:
        current = self.root
        while current is not None:
            if key < current.key:
                current = current.left
            elif key > current.key:
                current = current.right
            else:
                return True
        return False

    def delete(self, key: int) -> None:
        parent: Optional[BSTNode] = None
        current = self.root

        while current is not None and current.key != key:
            parent = current
            if key < current.key:
                current = current.left
            else:
                current = current.right

        if current is None:
            return

        # If both children exist, swap with in-order successor and remove successor.
        if current.left is not None and current.right is not None:
            succ_parent = current
            succ = current.right
            while succ.left is not None:
                succ_parent = succ
                succ = succ.left
            current.key = succ.key
            parent = succ_parent
            current = succ

        child = current.left if current.left is not None else current.right

        if parent is None:
            self.root = child
        elif parent.left is current:
            parent.left = child
        else:
            parent.right = child

        self.size -= 1

    @staticmethod
    def _min_node(node: BSTNode) -> BSTNode:
        current = node
        while current.left is not None:
            current = current.left
        return current


@dataclass
class AVLNode:
    key: int
    left: Optional["AVLNode"] = None
    right: Optional["AVLNode"] = None
    height: int = 1


class AVLTree:
    """AVL self-balancing tree with unique keys."""

    def __init__(self) -> None:
        self.root: Optional[AVLNode] = None
        self.size = 0

    def insert(self, key: int) -> None:
        self.root, inserted = self._insert_recursive(self.root, key)
        if inserted:
            self.size += 1

    def _insert_recursive(self, node: Optional[AVLNode], key: int) -> tuple[Optional[AVLNode], bool]:
        if node is None:
            return AVLNode(key), True

        if key < node.key:
            node.left, inserted = self._insert_recursive(node.left, key)
        elif key > node.key:
            node.right, inserted = self._insert_recursive(node.right, key)
        else:
            return node, False

        self._update_height(node)
        return self._rebalance(node), inserted

    def search(self, key: int) -> bool:
        current = self.root
        while current is not None:
            if key < current.key:
                current = current.left
            elif key > current.key:
                current = current.right
            else:
                return True
        return False

    def delete(self, key: int) -> None:
        self.root, deleted = self._delete_recursive(self.root, key)
        if deleted:
            self.size -= 1

    def _delete_recursive(self, node: Optional[AVLNode], key: int) -> tuple[Optional[AVLNode], bool]:
        if node is None:
            return None, False

        deleted = False
        if key < node.key:
            node.left, deleted = self._delete_recursive(node.left, key)
        elif key > node.key:
            node.right, deleted = self._delete_recursive(node.right, key)
        else:
            deleted = True
            if node.left is None:
                return node.right, True
            if node.right is None:
                return node.left, True
            successor = self._min_node(node.right)
            node.key = successor.key
            node.right, _ = self._delete_recursive(node.right, successor.key)

        if node is None:
            return None, deleted

        self._update_height(node)
        return self._rebalance(node), deleted

    @staticmethod
    def _min_node(node: AVLNode) -> AVLNode:
        current = node
        while current.left is not None:
            current = current.left
        return current

    @staticmethod
    def _height(node: Optional[AVLNode]) -> int:
        return node.height if node is not None else 0

    def _balance_factor(self, node: AVLNode) -> int:
        return self._height(node.left) - self._height(node.right)

    def _update_height(self, node: AVLNode) -> None:
        node.height = 1 + max(self._height(node.left), self._height(node.right))

    def _rebalance(self, node: AVLNode) -> AVLNode:
        balance = self._balance_factor(node)

        if balance > 1:
            if node.left is not None and self._balance_factor(node.left) < 0:
                node.left = self._rotate_left(node.left)
            return self._rotate_right(node)

        if balance < -1:
            if node.right is not None and self._balance_factor(node.right) > 0:
                node.right = self._rotate_right(node.right)
            return self._rotate_left(node)

        return node

    def _rotate_left(self, z: AVLNode) -> AVLNode:
        y = z.right
        if y is None:
            return z
        t2 = y.left

        y.left = z
        z.right = t2

        self._update_height(z)
        self._update_height(y)
        return y

    def _rotate_right(self, z: AVLNode) -> AVLNode:
        y = z.left
        if y is None:
            return z
        t3 = y.right

        y.right = z
        z.left = t3

        self._update_height(z)
        self._update_height(y)
        return y
