"""
Dynamic Hourglass Multi-Target Generator (Strictly Balanced Count Caps)
=============================================================================
Sweeps 3-glass spaces randomly, tests dynamic 3-step sequential targets, and evaluates 
the exact total number of unique midflips used alongside sequential synergy.

Strict Target Pool Count Ceilings:
- Rank 1 (0 midflips): Caps at exactly 25 items
- Rank 2 (1 midflip):  Caps at exactly 50 items
- Rank 3 (2 midflips): Caps at exactly 100 items
- Rank 4 (3 midflips): Caps at exactly 100 items

Outputs all data into a single unified file: 'multitarget_puzzles.txt'
"""

import itertools
from collections import deque
import json
import random

def solve_multitarget_sequence(sizes, target_sequence):
    """
    Simulates a sequential BFS across an exact glass set without state resets.
    Returns: (is_solvable, minimum_total_flips, distinct_mid_clock_flips)
    """
    n = len(sizes)
    initial_state = (tuple([0] * n), 0, 0, 0, frozenset())
    queue = deque([initial_state])
    visited = {}
    
    best_total_flips = float('inf')
    best_mid_count = -1

    while queue:
        rem, flips, t, seq_idx, mid_flipped = queue.popleft()
        current_goal = target_sequence[seq_idx]
        
        if t == current_goal:
            if seq_idx == len(target_sequence) - 1:
                if flips < best_total_flips:
                    best_total_flips = flips
                    best_mid_count = len(mid_flipped)
                continue
            else:
                seq_idx += 1
                current_goal = target_sequence[seq_idx]

        if t > current_goal or flips >= best_total_flips:
            continue

        state_key = (rem, t, seq_idx, mid_flipped)
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
                
                if new_t > current_goal:
                    continue
                    
                post_drain_rem = tuple(max(0, x - step) if x > 0 else 0 for x in next_rem)
                queue.append((post_drain_rem, flips + len(flip_indices), new_t, seq_idx, frozenset(next_mid_flipped)))

    if best_total_flips != float('inf'):
        return True, best_total_flips, best_mid_count
    return False, -1, -1


def generate_dynamic_multitarget_puzzles(output_filename="multitarget_puzzles.txt", max_glass_size=35):
    print("🚀 Initializing Randomized Multi-Target Sweep Pipeline with Target Caps...")
    print(f"Randomizing 3-glass triplets up to size {max_glass_size}m...")
    print("=" * 85)
    
    total_generated = 0
    
    # Precise user-defined target caps configuration matrix
    rank_caps = {1: 25, 2: 50, 3: 100, 4: 100}
    rank_counts = {1: 0, 2: 0, 3: 0, 4: 0}
    
    # Generate all possible sorted triplets within the range
    all_triplets = list(itertools.combinations(range(9, max_glass_size + 1), 3))
    
    # Shuffle the entire search list to guarantee organic randomness
    random.shuffle(all_triplets)
    
    with open(output_filename, "w", encoding="utf-8") as f:
        for triplet in all_triplets:
            
            # OPTIMIZATION TERMINATION: If all target metrics hit their ceiling limits, exit instantly
            if all(rank_counts[r] >= rank_caps[r] for r in rank_caps):
                break
                
            # Enforce non-consecutive constraint rules
            if (triplet[1] - triplet[0] == 1 or 
                triplet[2] - triplet[1] == 1 or 
                triplet[1] - triplet[0] == 2 or 
                triplet[2] - triplet[1] == 2 or 
                (triplet[2] - triplet[1] == triplet[1] - triplet[0])): 
                continue
            
            max_glass = max(triplet)
            
            # Randomize the target window spaces dynamically
            t1_options = list(range(max_glass + 1, max_glass + 5))
            random.shuffle(t1_options)
            
            triplet_resolved = False
            
            for t1 in t1_options:
                if triplet_resolved: 
                    break
                    
                t2_options = list(range(t1 + 3, t1 + 6))
                random.shuffle(t2_options)
                
                for t2 in t2_options:
                    if triplet_resolved: 
                        break
                        
                    t3_options = list(range(t2 + 4, t2 + 6))
                    random.shuffle(t3_options)
                    
                    for t3 in t3_options:
                        target_seq = (t1, t2, t3)
                        
                        # 1. Run main 3-glass solver sequence
                        success, min_flips, mid_flips = solve_multitarget_sequence(triplet, target_seq)
                        
                        if success:
                            # Map the midflips to their rank types
                            if mid_flips == 0:
                                rank_id = 1
                                rank_title = "Rank 1: Multi-Target Linear Tutorial"
                            elif mid_flips == 1:
                                rank_id = 2
                                rank_title = "Rank 2: Multi-Target Single Interruption"
                            elif mid_flips == 2:
                                rank_id = 3
                                rank_title = "Rank 3: Multi-Target Double Interruption"
                            elif mid_flips == 3:
                                rank_id = 4
                                rank_title = "Rank 4: Multi-Target Full Engine Cycle"
                            else:
                                continue
                                
                            # SKIP FILTER: If this specific rank has already hit its cap capacity, bypass
                            if rank_counts[rank_id] >= rank_caps[rank_id]:
                                continue
                                
                            # 2. Check for Sequential Synergy across all internal pairs
                            p1_ok, _, _ = solve_multitarget_sequence((triplet[0], triplet[1]), target_seq)
                            p2_ok, _, _ = solve_multitarget_sequence((triplet[0], triplet[2]), target_seq)
                            p3_ok, _, _ = solve_multitarget_sequence((triplet[1], triplet[2]), target_seq)
                            
                            is_synergistic = (not p1_ok and not p2_ok and not p3_ok)
                            
                            if not is_synergistic:
                                continue
                            
                            # Build unified layout entry
                            entry = {
                                "config": [list(triplet), list(target_seq), min_flips],
                                "midflips": mid_flips,
                                "rank": rank_id,
                                "rank_name": rank_title
                            }
                            
                            f.write(json.dumps(entry) + "\n")
                            total_generated += 1
                            rank_counts[rank_id] += 1
                            
                            triplet_resolved = True
                            
                            print(f"✨ Level {total_generated:03d}: Glasses {triplet} ➔ Targets {target_seq} | Rank: {rank_id} ({rank_counts[rank_id]}/{rank_caps[rank_id]}) | Flips: {min_flips} | Synergy: YES 💎")
                            break
                    if triplet_resolved:
                        break
                if triplet_resolved:
                    break

    print("=" * 85)
    print(f"🎉 Success! Search complete. Exported exactly {total_generated} custom puzzles to '{output_filename}'.")
    print("Final Balanced Dataset Summary:")
    for r_id in sorted(rank_caps.keys()):
        print(f"  -> Rank {r_id} Total Compiled: {rank_counts[r_id]} / {rank_caps[r_id]}")


if __name__ == "__main__":
    generate_dynamic_multitarget_puzzles()
