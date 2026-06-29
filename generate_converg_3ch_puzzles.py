import heapq
import random
import time

NUM_GLASSES = 6
# Precompute popcount (number of set bits) for all 64 possible flip combinations
POP_COUNT = [bin(i).count('1') for i in range(1 << NUM_GLASSES)]

def solve_convergence_puzzle_3ch(sizes, target, max_flips_cap=13):
    """
    Hyper-optimized Dijkstra solver for 3-channel convergence.
    Unrolled loops, bitmasked operations, zero path tracking.
    """
    s0, s1, s2, s3, s4, s5 = sizes
    
    counter = 0
    # Heap: (num_flips, tie_breaker, rem_tuple, time, midflipped_mask)
    # NOTE: The last element is now a BITMASK of which glasses have been mid-flipped, not the count!
    heap = [(0, counter, (0, 0, 0, 0, 0, 0), 0, 0)]
    
    # State tracking: visited[(rem, t)] = array of 7 minimum-flips for each possible unique mid_count (0..6)
    visited = {}
    
    best_flips = float('inf')
    best_mids = 0

    while heap:
        # Pop the mask from the heap
        flips, _, rem, t, cur_mid_mask = heapq.heappop(heap)
        
        # Calculate the actual 0-6 count of unique glasses mid-flipped
        cur_mids = POP_COUNT[cur_mid_mask]
        
        # If we already found a better or equal solution, skip
        if flips >= best_flips:
            continue
            
        if t == target:
            if cur_mids > 0:
                if flips < best_flips:
                    best_flips = flips
                    best_mids = cur_mids
                elif flips == best_flips and cur_mids > best_mids:
                    best_mids = cur_mids
            continue

        state_key = (rem, t)
        min_flips_arr = visited.get(state_key)
        if min_flips_arr is None:
            min_flips_arr = [float('inf')] * 7
            visited[state_key] = min_flips_arr
            
        # Prune if we reached this state+midcount with fewer or equal flips before
        if min_flips_arr[cur_mids] <= flips:    
            continue
        min_flips_arr[cur_mids] = flips

        # Fast bitmask check: which glasses are currently mid-flipped? (0 < rem < size)
        mid_state = 0
        if 0 < rem[0] < s0: mid_state |= 1
        if 0 < rem[1] < s1: mid_state |= 2
        if 0 < rem[2] < s2: mid_state |= 4
        if 0 < rem[3] < s3: mid_state |= 8
        if 0 < rem[4] < s4: mid_state |= 16
        if 0 < rem[5] < s5: mid_state |= 32

        # Try all 64 flip combinations natively
        for flip_mask in range(1 << NUM_GLASSES):
            cost = POP_COUNT[flip_mask]
            new_flips = flips + cost
            
            # Early aggressive pruning
            if new_flips >= best_flips or new_flips >= max_flips_cap:
                continue
                
            # Unrolled flip execution (No lists, pure C-level variable assignment)
            n0 = s0 - rem[0] if (flip_mask & 1) else rem[0]
            n1 = s1 - rem[1] if (flip_mask & 2) else rem[1]
            n2 = s2 - rem[2] if (flip_mask & 4) else rem[2]
            n3 = s3 - rem[3] if (flip_mask & 8) else rem[3]
            n4 = s4 - rem[4] if (flip_mask & 16) else rem[4]
            n5 = s5 - rem[5] if (flip_mask & 32) else rem[5]
            
            # Unrolled channel active checks & minimums (Alpha, Beta, Gamma)
            if n0 == 0 and n1 == 0: continue
            min_A = n0 if n0 > 0 and (n1 == 0 or n0 <= n1) else n1
            
            if n2 == 0 and n3 == 0: continue
            min_B = n2 if n2 > 0 and (n3 == 0 or n2 <= n3) else n3
            
            if n4 == 0 and n5 == 0: continue
            min_C = n4 if n4 > 0 and (n5 == 0 or n4 <= n5) else n5

            step = min_A if min_A <= min_B and min_A <= min_C else (min_B if min_B <= min_C else min_C)
            new_t = t + step
            
            if new_t > target:
                continue
                
            # Last step convergence constraints
            if new_t == target:
                if cost != 1: continue
                # Isolate lowest set bit to find the single flipped index instantly
                flipped_idx = (flip_mask & -flip_mask).bit_length() - 1
                if rem[flipped_idx] == 0: continue
                if not (min_A == min_B == min_C): continue
            
            # Unrolled drain execution (mathematically guaranteed >= 0, no max() needed)
            p0 = n0 - step if n0 > 0 else 0
            p1 = n1 - step if n1 > 0 else 0
            p2 = n2 - step if n2 > 0 else 0
            p3 = n3 - step if n3 > 0 else 0
            p4 = n4 - step if n4 > 0 else 0
            p5 = n5 - step if n5 > 0 else 0
            
            # --- THE FIX IS HERE ---
            # Use Bitwise OR (|) to accumulate UNIQUE glasses that have been mid-flipped
            new_mid_mask = cur_mid_mask | (flip_mask & mid_state)
            
            # Push the MASK to the heap, not the count!
            heapq.heappush(heap, (new_flips, counter, (p0, p1, p2, p3, p4, p5), new_t, new_mid_mask))
            counter += 1

    if best_flips != float('inf'):
        return best_flips, best_mids
    return None, 0

def generate_random_3channel_puzzles(target_count=50):
    print(f"🚀 Initializing Hyper-Optimized 3-Channel Puzzle Generator (Target: {target_count})...\n")

    pool = list(range(5, 19))
    seen_combos = set()

    midflip_distribution = {i: 0 for i in range(7)}
    solved_puzzles = []
    attempts = 0
    skipped_seen = 0
    start_time = time.time()

    with open("convergence_puzzles5.txt", "w", encoding="utf-8") as f_out:

        while len(solved_puzzles) < target_count:
            attempts += 1

            six = random.sample(pool, 6)
            random.shuffle(six)
            ch_a = tuple(sorted([six[0], six[1]]))
            ch_b = tuple(sorted([six[2], six[3]]))
            ch_c = tuple(sorted([six[4], six[5]]))

            channels = sorted([ch_a, ch_b, ch_c], key=lambda x: x[0])
            combo_key = tuple(channels)
            
            if combo_key in seen_combos:
                skipped_seen += 1
                continue
            seen_combos.add(combo_key)

            sizes = channels[0] + channels[1] + channels[2]
            max_glass = max(sizes)

            found = False
            t_options = list(range(max_glass + 1, max_glass + 5))
            random.shuffle(t_options)
            for target in t_options:
                solve_start = time.time()
                flips, mid_count = solve_convergence_puzzle_3ch(sizes, target)
                solve_time = time.time() - solve_start
                print(solve_time)

                if flips:
                    puzzle_data = {
                        "config": [list(sizes), target, flips],
                        "midflips": mid_count,
                        "rank": 3,
                        "rank_name": "Rank 3: Triple Channel Harmony"
                    }
                    f_out.write(f"{puzzle_data}\n")

                    solved_puzzles.append(puzzle_data)
                    midflip_distribution[mid_count] += 1
                    found = True

                    elapsed = time.time() - start_time
                    print(f"  ✅ #{len(solved_puzzles):3d} | {sizes} → {target}m | "
                          f"{flips} flips | {mid_count} midflips | "
                          f"solve: {solve_time:.3f}s | total: {elapsed:.0f}s")
                    break

            if not found and attempts % 200 == 0:
                elapsed = time.time() - start_time
                print(f"  ⏳ {attempts} attempts, {len(solved_puzzles)} found, "
                      f"{skipped_seen} dupes skipped | {elapsed:.0f}s elapsed")

    elapsed = time.time() - start_time
    print("\n" + "=" * 70)
    print(f"🏁 GENERATION COMPLETE in {elapsed:.1f}s")
    print(f"   Total attempts: {attempts}")
    print(f"   Duplicates skipped: {skipped_seen}")
    print(f"   Valid puzzles found: {len(solved_puzzles)}")
    if attempts > 0:
        print(f"   Hit rate: {len(solved_puzzles) / attempts * 100:.1f}%")
    print("\nMidflip distribution:")
    for count, freq in sorted(midflip_distribution.items()):
        if freq > 0:
            print(f"  • {count} unique glasses midflip: {freq} puzzles")
    print("\nResults saved to 'convergence_puzzles4.txt'")
    print("=" * 70)


if __name__ == "__main__":
    generate_random_3channel_puzzles(target_count=200)