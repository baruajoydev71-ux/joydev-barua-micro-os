#!/bin/bash
# Experiment 1.6: Bash Conditional Logic (Joydev Barua - 25BTRCL298)

echo "=== Part A: Even or Odd Verification ==="
echo -n "Enter an integer: "
read -r n
echo "$n"
if (( n % 2 == 0 )); then
    echo "Result: $n is an EVEN number."
else
    echo "Result: $n is an ODD number."
fi

echo ""
echo "=== Part B: Leap Year Verification ==="
echo -n "Enter a year: "
read -r y
echo "$y"
if (( (y % 4 == 0 && y % 100 != 0) || (y % 400 == 0) )); then
    echo "Result: $y is a LEAP year."
else
    echo "Result: $y is NOT a leap year."
fi
