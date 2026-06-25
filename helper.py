#solve
import itertools
from collections import deque

def solve_hourglass_clean(sizes, target):
    """
    Finds the absolute minimum-flip sequence to measure target minutes.
    Tracks and prints the number of distinct hourglass sizes flipped mid-clock.
    """
    n = len(sizes)
    # Queue structure: (tuple_of_remaining_sand, total_flips, current_time, action_list, mid_flipped_indices_frozenset)
    initial_state = (tuple([0] * n), 0, 0, [], frozenset())
    queue = deque([initial_state])
    visited = {}
    
    best_flips = float('inf')
    best_actions = None
    best_mid_count = 0
    
    while queue:
        rem, flips, t, actions, mid_flipped = queue.popleft()
        
        if t == target:
            if flips < best_flips:
                best_flips = flips
                best_actions = actions
                best_mid_count = len(mid_flipped)
            continue
            
        if t > target or flips >= best_flips:
            continue
            
        # Visited check tracking sand levels, current time, and mid-flip histories
        state_key = (rem, t, mid_flipped)
        if state_key in visited and visited[state_key] <= flips:
            continue
        visited[state_key] = flips
        
        # Evaluate all combinations of flips at time t
        for r in range(n + 1):
            for flip_indices in itertools.combinations(range(n), r):
                next_rem = list(rem)
                added_flips = len(flip_indices)
                
                next_mid_flipped = set(mid_flipped)
                for idx in flip_indices:
                    # Mid-clock condition: sand is strictly between empty (0) and max capacity
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
                
                # Record the configuration directly AFTER the flips happen at time t
                new_actions = list(actions)
                if added_flips > 0:
                    new_actions.append((t, "flip", list(flip_indices), tuple(next_rem)))
                
                # If we successfully reach the target time, record the final step details
                if new_t == target:
                    finishing = [i for i, x in enumerate(next_rem) if x == step]
                    new_actions.append((new_t, "finishes", finishing, post_drain_rem))
                    
                queue.append((post_drain_rem, flips + added_flips, new_t, new_actions, frozenset(next_mid_flipped)))
                
    print(f"Hourglasses: {sizes} | Target: {target} min")
    print("-" * 65)
    
    if not best_actions:
        print("Not possible\n")
        return
        
    for t_act, type_act, indices, state in best_actions:
        state_info = f"({', '.join(f'{state[i]}' for i in range(n))})"
        
        if type_act == "flip":
            names = " and ".join(str(sizes[i]) for i in indices)
            print(f"at t={t_act:2d}, flip {names:<15s} {state_info}")
        elif type_act == "finishes":
            names = " and ".join(str(sizes[i]) for i in indices)
            print(f"at t={t_act:2d}, {names:<20s} {state_info} | total flips: {best_flips} | distinct mid flips: {best_mid_count}")
    print()

# Test cases
solve_hourglass_clean([9,13,15],20)

"""
Hourglass Multi-Target Sequential Engine & Generator
=====================================================
A toolkit for designing, solving, and exporting puzzles where a SINGLE set
of hourglass capacities must measure multiple distinct target markers in a 
strict sequential timeline (e.g., hitting 18m, then 21m, then 33m).

Crucially, the sand states DO NOT RESET between targets. The puzzle engine 
must solve target N starting from the exact residue sand configuration left over 
from completing target N-1.
"""

import itertools
from collections import deque
import json

def solve_multitarget_sequence(sizes, target_sequence):
    """
    Finds the absolute minimum-flip chronological sequence to hit a series 
    of target time markers in sequential order without state resets.

    Args:
        sizes (tuple[int, ...]): Capacities of the available hourglasses.
        target_sequence (tuple[int, ...]): Ordered list of cumulative targets 
            to hit (e.g., (18, 21, 33)). Note: Targets are absolute times from t=0.

    Returns:
        dict: A structured summary of the solution route:
            {
                "success": bool,
                "total_flips": int,
                "actions": list[tuple] # List of all chronologically executed moves
            }
    """
    n = len(sizes)
    
    # Verify the sequence is strictly increasing
    if any(target_sequence[i+1] <= target_sequence[i] for i in range(len(target_sequence) - 1)):
        return {"success": False, "total_flips": -1, "actions": []}

    # Queue layout: (remaining_sand, current_flips, current_time, action_history, sequence_index)
    # Start at t=0, looking for target_sequence[0]
    initial_state = (tuple([0] * n), 0, 0, [], 0)
    queue = deque([initial_state])
    
    # Visited tracking key: (remaining_sand_tuple, current_time, sequence_index) -> mapped to minimum flips
    visited = {}
    
    best_total_flips = float('inf')
    best_actions = []

    while queue:
        rem, flips, t, actions, seq_idx = queue.popleft()
        
        # Check if the current milestone target in the sequence is hit
        current_goal = target_sequence[seq_idx]
        
        if t == current_goal:
            # If this was the final target in the sequence, we found a complete solution path!
            if seq_idx == len(target_sequence) - 1:
                if flips < best_total_flips:
                    best_total_flips = flips
                    best_actions = actions
                continue
            else:
                # Advance to looking for the next target marker in the sequence using current sand residue
                seq_idx += 1
                current_goal = target_sequence[seq_idx]

        # Prune branches that overshot the active target or are less efficient than our current best par
        if t > current_goal or flips >= best_total_flips:
            continue

        state_key = (rem, t, seq_idx)
        if state_key in visited and visited[state_key] <= flips:
            continue
        visited[state_key] = flips

        # Evaluate all split flip combinations at this specific event boundary
        for r in range(n + 1):
            for flip_indices in itertools.combinations(range(n), r):
                next_rem = list(rem)
                added_flips = len(flip_indices)
                
                for idx in flip_indices:
                    next_rem[idx] = sizes[idx] - next_rem[idx]
                    
                active = [x for x in next_rem if x > 0]
                if not active:
                    continue
                    
                step = min(active)
                new_t = t + step
                
                # Cannot skip past our current active checkpoint target
                if new_t > current_goal:
                    continue
                    
                post_drain_rem = tuple(max(0, x - step) if x > 0 else 0 for x in next_rem)
                
                # Build narrative logging steps
                new_actions = list(actions)
                if added_flips > 0:
                    new_actions.append((t, "flip", list(flip_indices), tuple(next_rem)))
                
                # Document if an exact target marker milestone was triggered
                if new_t == current_goal:
                    new_actions.append((new_t, "TARGET_HIT", seq_idx, post_drain_rem))
                else:
                    finishing = [i for i, x in enumerate(next_rem) if x == step]
                    new_actions.append((new_t, "drain_event", finishing, post_drain_rem))

                queue.append((post_drain_rem, flips + added_flips, new_t, new_actions, seq_idx))

    if best_total_flips != float('inf'):
        return {"success": True, "total_flips": best_total_flips, "actions": best_actions}
    return {"success": False, "total_flips": -1, "actions": []}


def print_multitarget_walkthrough(sizes, target_sequence):
    """
    Solves a multi-target puzzle and outputs a beautifully clean, line-by-line
    chronological narrative showing exactly how the sand states morph between milestones.
    """
    print(f"⌛ MULTI-TARGET PUZZLE: Glasses {sizes}")
    print(f"🎯 SEQUENCE GOALS     : {' ➔ '.join(f'{tgt}m' for tgt in target_sequence)}")
    print("=" * 70)
    
    result = solve_multitarget_sequence(sizes, target_sequence)
    if not result["success"]:
        print("❌ This exact sequence is mathematically impossible with these glasses.\n")
        return

    n = len(sizes)
    for t_act, act_type, meta, state in result["actions"]:
        state_str = f"({', '.join(str(state[i]) for i in range(n))})"
        
        if act_type == "flip":
            names = " and ".join(f"{sizes[i]}m" for i in meta)
            print(f"  at t={t_act:2d}m | FLIP {names:<15s} Current Sand Bars: {state_str}")
        elif act_type == "drain_event":
            names = " and ".join(f"{sizes[i]}m" for i in meta)
            print(f"  at t={t_act:2d}m | {names:<20s} emptied. Remaining:  {state_str}")
        elif act_type == "TARGET_HIT":
            print(f"  ✨ [t={t_act:2d}m] CHRONO TARGET #{meta+1} SECURED! Handing off sand: {state_str}")
            
    print("=" * 70)
    print(f"🎉 SUCCESS! Sequence completed perfectly using {result['total_flips']} total flips.\n")

# =====================================================================
# PIPELINE DEMONSTRATION RUN
# =====================================================================
if __name__ == "__main__":
    # Demo 1: Run your signature concept puzzle
    # Can glasses (8, 13, 21) measure 18m, then 21m, then 33m sequentially?
    #Glasses (9, 16, 30) ➔ Targets (34, 39, 43)
    sample_glasses = (9,16,30)
    sample_sequence = (34,39,43)
    print_multitarget_walkthrough(sample_glasses, sample_sequence)