#!/usr/bin/env python3
"""Independent unsigned-32 oracles for the T-0191 program inputs."""

from __future__ import annotations

import json

MASK = (1 << 32) - 1


def u32(value: int) -> int:
    return value & MASK


def neighborhood() -> int:
    grid = (
        (1, 2, 3, 4),
        (5, 6, 7, 8),
        (9, 10, 11, 12),
        (13, 14, 15, 16),
    )
    total = 0
    for row in (1, 2):
        for col in (1, 2):
            total = u32(total + sum((
                grid[row][col],
                grid[row - 1][col],
                grid[row + 1][col],
                grid[row][col - 1],
                grid[row][col + 1],
            )))
    return total


def elementwise() -> int:
    return u32(sum(value * 3 + 7 for value in (3, 5, 8, 13, 21, 34, 55, 89)))


def reduction() -> int:
    return u32(sum((0xFFFFFFFF, 1, 2, 3, 5, 8, 13, 21, 34, 55, 89, 144)))


def main() -> None:
    print(json.dumps({
        "elementwise": elementwise(),
        "neighborhood": neighborhood(),
        "reduction": reduction(),
    }, sort_keys=True))


if __name__ == "__main__":
    main()
