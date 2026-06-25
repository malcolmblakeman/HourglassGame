"""
Unified Hourglass Level Generator
=================================
Sweeps structural search grids across 2-glass and 3-glass spaces,
validates path flip metrics, and saves all matching puzzle configurations 
into a single text file named 'all_hourglass_puzzles.txt'.

Outputs lines matching format schema:
{"config": ((a, b, c), target, min_flips), "rank": x, "rank_name": "Label"}
"""

import itertools
from collections import deque
import json

def solve_hourglass_puzzle(sizes, target):
    """
    Simulates a BFS search over an exact glass set to return:
    (is_solvable, minimum_total_flips, distinct_mid_clock_flips)
    """
    n = len(sizes)
    # Queue structure: (tuple_remaining_sand, total_flips, current_time, mid_flipped_indices_frozenset)
    initial_state = (tuple([0] * n), 0, 0, frozenset())
    queue = deque([initial_state])
    visited = {}
    
    best_flips = float('inf')
    best_mid_count = -1
    
    while queue:
        rem, flips, t, mid_flipped = queue.popleft()
        
        if t == target:
            if flips < best_flips:
                best_flips = flips
                best_mid_count = len(mid_flipped)
            continue
            
        if t > target or flips >= best_flips:
            continue
            
        state_key = (rem, t, mid_flipped)
        if state_key in visited and visited[state_key] <= flips:
            continue
        visited[state_key] = flips
        
        for r in range(n + 1):
            for flip_indices in itertools.combinations(range(n), r):
                next_rem = list(rem)
                next_mid_flipped = set(mid_flipped)
                
                for idx in flip_indices:
                    if 0 < rem[idx] < sizes[idx]:
                        next_mid_flipped.add(idx)
                    next_rem[idx] = sizes[idx] - next_rem[idx]
                    
                active = [x for x in next_rem if x > 0]
                if not active:
                    continue
                    
                step = min(active)
                new_t = t + step
                if new_t > target:
                    continue
                    
                post_drain_rem = tuple(max(0, x - step) if x > 0 else 0 for x in next_rem)
                queue.append((post_drain_rem, flips + len(flip_indices), new_t, frozenset(next_mid_flipped)))
                
    if best_flips != float('inf'):
        return True, best_flips, best_mid_count
    return False, -1, -1


def generate_unlimited_puzzle_pool(output_filename="all_hourglass_puzzles.txt"):
    print("🚀 Commencing Unlimited Level Generation Loop...")
    
    total_written = 0
    rank_counts = {i: 0 for i in range(1, 9)}
    
    with open(output_filename, "w", encoding="utf-8") as f:
        # -------------------------------------------------------------
        # SWEEP A: 2 Glasses (Ranks 1, 2, 3)
        # -------------------------------------------------------------
        print("-> Processing 2-Glass space matrix...")
        for pair in itertools.combinations(range(3, 18), 2):
            if pair[1] - pair[0] == 1: 
                continue
                
            for target in range(4, 30):
                success, flips, mid_count = solve_hourglass_puzzle(pair, target)
                if not success: 
                    continue
                    
                entry = None
                # Rank 1: 2 Glasses, 0 Midflips
                if mid_count == 0:
                    entry = {"config": (pair, target, flips), "rank": 1, "rank_name": "Rank 1: The Linear Tutorial"}
                # Rank 2: 2 Glasses, 1 Midflip Required
                elif mid_count == 1:
                    entry = {"config": (pair, target, flips), "rank": 2, "rank_name": "Rank 2: One Midflip"}
                # Rank 3: 2 Glasses, 2 Midflips Required
                elif mid_count == 2:
                    entry = {"config": (pair, target, flips), "rank": 3, "rank_name": "Rank 3: Two Midflips"}
                
                if entry:
                    f.write(json.dumps(entry) + "\n")
                    rank_counts[entry["rank"]] += 1
                    total_written += 1

        # -------------------------------------------------------------
        # SWEEP B: 3 Glasses (Ranks 4 to 8)
        # -------------------------------------------------------------
        print("-> Processing 3-Glass space matrix...")
        for triplet in itertools.combinations(range(4, 30), 3):
            if triplet[1] - triplet[0] == 1 or triplet[2] - triplet[1] == 1: 
                continue
                
            for target in range(20, 40):
                # Optimization rule: Skip if target is less than the largest element inside the triplet
                if target < max(triplet): 
                    continue
                    
                success, flips, mid_count = solve_hourglass_puzzle(triplet, target)
                if not success: 
                    continue
                    
                # Sub-pair solver sequences to check for cooperative synergy
                p1_ok, _, _ = solve_hourglass_puzzle((triplet[0], triplet[1]), target)
                p2_ok, _, _ = solve_hourglass_puzzle((triplet[0], triplet[2]), target)
                p3_ok, _, _ = solve_hourglass_puzzle((triplet[1], triplet[2]), target)
                is_synergistic = (not p1_ok and not p2_ok and not p3_ok)
                
                entry = None
                
                if not is_synergistic:
                    # Rank 4: 3 Glasses, 1 Midflip
                    if mid_count == 1:
                        entry = {"config": (triplet, target, flips), "rank": 4, "rank_name": "Rank 4: One Midflip, Three Glasses"}
                    # Rank 5: 3 Glasses, 2 Midflips
                    elif mid_count == 2:
                        entry = {"config": (triplet, target, flips), "rank": 5, "rank_name": "Rank 5: Two Midflips, Three Glasses"}
                    # Rank 6: 3 Glasses, 3 Midflips
                    elif mid_count == 3:
                        entry = {"config": (triplet, target, flips), "rank": 6, "rank_name": "Rank 6: Three Midflips, Three Glasses"}
                else:
                    # Rank 7: 3 Glasses, 2 Midflips + Synergy
                    if mid_count == 2:
                        entry = {"config": (triplet, target, flips), "rank": 7, "rank_name": "Rank 7: Synergistic Two Midflips"}
                    # Rank 8: 3 Glasses, 3 Midflips + Synergy
                    elif mid_count == 3:
                        entry = {"config": (triplet, target, flips), "rank": 8, "rank_name": "Rank 8: Synergistic Three Midflips"}
                
                if entry:
                    f.write(json.dumps(entry) + "\n")
                    rank_counts[entry["rank"]] += 1
                    total_written += 1

    print("\n" + "=" * 55)
    print(f"SUCCESS: {total_written} unique puzzles written to '{output_filename}'")
    print("=" * 55)
    for rank_id, count in rank_counts.items():
        print(f" -> Rank {rank_id} Total Compiled: {count}")


if __name__ == "__main__":
    generate_unlimited_puzzle_pool()
