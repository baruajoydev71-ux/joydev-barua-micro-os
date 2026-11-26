#!/bin/bash
# Experiment 1.7: Factorial Iteration & Variable Swapping (Joydev Barua)

echo "=== Part A: Iterative Factorial Computation ==="
echo -n "Enter a positive integer: "
read -r n
echo "$n"
fact=1
num=$n
while [ "$num" -gt 1 ]; do
    fact=$(( fact * num ))
    num=$(( num - 1 ))
done
echo "Factorial of $n ($n!) = $fact"

echo ""
echo "=== Part B: Variable Value Swapping ==="
echo -n "Enter two numbers (a b): "
read -r a b
echo "$a $b"
echo "Before swap: a = $a, b = $b"
temp=$a
a=$b
b=$temp
echo "After swap:  a = $a, b = $b"
