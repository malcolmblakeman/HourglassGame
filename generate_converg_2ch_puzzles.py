import itertools
from collections import deque

def solve_convergence_puzzle(sizes, target, len_A):
    """
    Finds and returns the absolute shortest-flip path satisfying all Convergence rules:
    - Both channels must stay active at every step.
    - Last step (hitting target) must:
        - Have exactly 1 flip.
        - That single flip must be of a glass that was NOT empty (rem > 0).
        - Both channels must end at the exact same time (min_A == min_B on the last step).
    - The path must contain at least one midflip.
    - Every single hourglass must be flipped at least once during the path.
    
    Returns:
        (best_path, best_midflip_count, best_flips) or (None, 0, float('inf'))
    """
    n = len(sizes)
    labels = []
    for i, s in enumerate(sizes):
        if i < len_A:
            labels.append(f"Alpha-{s}m")
        else:
            labels.append(f"Beta-{s}m")

    # Queue element layout: (rem, current_time, midflip_mask, flipped_mask, path_history)
    # midflip_mask tracks WHICH unique hourglasses have undergone a midflip
    initial_state = ((0,) * n, 0, 0, 0, [])
    queue = deque([initial_state])
    visited = {}

    best_flips = float('inf')
    best_path = None
    best_midflip_count = 0

    # Bitmask representing all hourglasses flipped at least once
    target_mask = (1 << n) - 1

    while queue:
        rem, t, mid_mask, mask, path = queue.popleft()

        if t == target:
            # Calculate how many unique hourglasses did a midflip
            unique_midflips = bin(mid_mask).count('1')
            
            # Enforce validation criteria: at least 1 unique glass midflipped AND all glasses used
            if unique_midflips > 0 and mask == target_mask:
                total_flips = sum(len(step[1]) for step in path)
                if total_flips < best_flips:
                    best_flips = total_flips
                    best_path = path
                    best_midflip_count = unique_midflips
            continue

        total_flips = sum(len(step[1]) for step in path)
        if t > target or total_flips >= best_flips:
            continue

        state_key = (rem, t, mid_mask, mask)
        if state_key in visited and visited[state_key] <= total_flips:
            continue
        visited[state_key] = total_flips

        # Explore all combinations of flips
        for r in range(n + 1):
            for flip_indices in itertools.combinations(range(n), r):
                next_rem = list(rem)
                new_mid_mask = mid_mask
                new_mask = mask
                
                # Execute flips and track metrics
                for idx in flip_indices:
                    if 0 < rem[idx] < sizes[idx]:
                        new_mid_mask |= (1 << idx)  # Track UNIQUE hourglass midflips via bitmask
                    next_rem[idx] = sizes[idx] - next_rem[idx]
                    new_mask |= (1 << idx)  # Record that this hourglass was flipped at least once

                # Check active sand flow in both channels
                active_A = [next_rem[i] for i in range(len_A) if next_rem[i] > 0]
                active_B = [next_rem[i] for i in range(len_A, n) if next_rem[i] > 0]
                
                if not active_A or not active_B:
                    continue  # Invalid step: both channels must flow

                min_A = min(active_A)
                min_B = min(active_B)
                step = min(min_A, min_B)
                new_t = t + step

                if new_t > target:
                    continue

                # Last step convergence constraints
                if new_t == target:
                    if len(flip_indices) != 1:
                        continue
                    flipped_idx = flip_indices[0]
                    if rem[flipped_idx] == 0:
                        continue
                    if min_A != min_B:
                        continue

                post_drain_rem = tuple(max(0, x - step) if x > 0 else 0 for x in next_rem)
                
                new_path = list(path)
                flip_labels = [labels[idx] for idx in flip_indices]
                new_path.append((rem, flip_labels, step, post_drain_rem, new_t))
                
                queue.append((post_drain_rem, new_t, new_mid_mask, new_mask, new_path))

    return best_path, best_midflip_count, best_flips


def generate_and_verify_puzzles():
    """
    Uses nested for loops to sequentially generate unique puzzle variations,
    filtering them dynamically using the bitmasked state checker.
    """
    print(f"🚀 Initializing automatic loop-driven puzzle generator...\n")
    
    # Pre-generate all valid unique channels (2 distinct elements where c1 < c2)
    valid_channels = []
    for c1 in range(3, 16):
        for c2 in range(c1 + 1, c1 + 6):
            valid_channels.append((c1, c2))
    
    # Track the distribution based on unique glasses midflipped (0 to 4 possible for 4 glasses)
    midflip_distribution = {0: 0, 1: 0, 2: 0, 3: 0, 4: 0}
    solved_puzzles_count = 0
    
    # Open the text file for writing results line by line
    with open("convergence_puzzles2.txt", "w", encoding="utf-8") as f_out:
        
        # Combine pairs of channels without duplicating or overlapping values
        for alpha_chan, base_beta_chan in itertools.product(valid_channels, repeat=2):
        
            # Shift both values of the Beta channel up by 2
            beta_chan = (base_beta_chan[0] + 2, base_beta_chan[1] + 2)
            
            # Eliminate channel-level symmetry
            if alpha_chan > beta_chan:
                continue
                
            # Ensure all 4 numbers across both channels are strictly unique
            if len(set(alpha_chan + beta_chan)) == 4:
                alpha1, alpha2 = alpha_chan
                beta1, beta2 = beta_chan
                if (alpha2 - alpha1) == (beta2 - beta1):
                    continue
            else:
                continue
                            
            sizes = (alpha1, alpha2, beta1, beta2)
            len_A = 2
            max_glass = max(sizes)
            t_options = list(range(max_glass + 1, max_glass + 6))
            
            for target in t_options:
                path, mid_count, flips = solve_convergence_puzzle(sizes, target, len_A)
                if path:
                    # Construct data dictionary structure matching requested syntax
                    puzzle_data = {
                        "config": [list(sizes), target, flips],
                        "midflips": mid_count,
                        "rank": 1,
                        "rank_name": "Rank 1: Two Channels"
                    }
                    
                    # Write exact string formatting to file followed by newline
                    f_out.write(f"{puzzle_data}\n")
                    
                    midflip_distribution[mid_count] += 1
                    solved_puzzles_count += 1
                    break  # Proceed to the next unique puzzle variation
                
    print("=" * 60)
    print(f"🏁 ALL PUZZLES PROCESSED (Total Unique Puzzles: {solved_puzzles_count})")
    print("Distribution of UNIQUE hourglasses that do a midflip:")
    for count, frequency in sorted(midflip_distribution.items()):
        print(f"  • Puzzles where exactly {count} unique glasses midflip: {frequency}")
    print("Results successfully saved to 'convergence_puzzles.txt'")
    print("=" * 60)


if __name__ == "__main__":
    generate_and_verify_puzzles()
