import streamlit as st
import itertools
from collections import deque
import random

# =====================================================================
# 1. PATHFINDING HINT ENGINE (BFS SOLVER)
# =====================================================================
def find_next_best_step(current_state, sizes, target, current_time):
    """
    Simulates the puzzle space starting from the current mid-game board state.
    Returns the exact list of glass labels that should be flipped right now
    to stay on (or find) the absolute shortest-flip path to victory.
    """
    n = len(sizes)
    labels = [f"{s}m" for s in sizes]
    
    # Queue layout: (tuple_remaining_sand, total_flips, current_time, first_action_indices)
    initial_state = (current_state, 0, current_time, None)
    queue = deque([initial_state])
    visited = {}
    
    best_flips = float('inf')
    optimal_first_action = None

    while queue:
        rem, flips, t, first_action = queue.popleft()
        
        if t == target:
            if flips < best_flips:
                best_flips = flips
                optimal_first_action = first_action
            continue
            
        if t > target or flips >= best_flips:
            continue
            
        state_key = (rem, t)
        if state_key in visited and visited[state_key] <= flips:
            continue
        visited[state_key] = flips
        
        # Evaluate all combinations of flip subsets at this state step
        for r in range(n + 1):
            for flip_indices in itertools.combinations(range(n), r):
                next_rem = list(rem)
                
                for idx in flip_indices:
                    next_rem[idx] = sizes[idx] - next_rem[idx]
                    
                active = [x for x in next_rem if x > 0]
                if not active:
                    continue
                    
                step = min(active)
                new_t = t + step
                if new_t > target:
                    continue
                    
                post_drain_rem = tuple(max(0, x - step) if x > 0 else 0 for x in next_rem)
                
                # Capture only the first choice of this branch timeline
                current_action = list(flip_indices) if first_action is None else first_action
                
                queue.append((post_drain_rem, flips + len(flip_indices), new_t, current_action))
                
    if optimal_first_action is not None:
        return [labels[i] for i in optimal_first_action]
    return None

def find_next_best_multitarget_step(current_state, sizes, target_sequence, current_time):
    """
    BFS simulation across the remaining targets in a multi-target sequence.
    Returns the exact list of labels to flip RIGHT NOW to guarantee long-term victory.
    """
    n = len(sizes)
    labels = [f"{s}m" for s in sizes]
    
    # Queue: (remaining_sand, total_flips, current_time, sequence_index, first_action_labels)
    initial_state = (current_state, 0, current_time, 0, None)
    queue = deque([initial_state])
    visited = {}
    
    best_total_flips = float('inf')
    optimal_first_action = None

    while queue:
        rem, flips, t, seq_idx, first_action = queue.popleft()
        current_goal = target_sequence[seq_idx]
        
        if t == current_goal:
            if seq_idx == len(target_sequence) - 1:
                if flips < best_total_flips:
                    best_total_flips = flips
                    optimal_first_action = first_action
                continue
            else:
                seq_idx += 1
                current_goal = target_sequence[seq_idx]

        if t > current_goal or flips >= best_total_flips:
            continue

        state_key = (rem, t, seq_idx)
        if state_key in visited and visited[state_key] <= flips:
            continue
        visited[state_key] = flips

        for r in range(n + 1):
            for flip_indices in itertools.combinations(range(n), r):
                next_rem = list(rem)
                for idx in flip_indices:
                    next_rem[idx] = sizes[idx] - next_rem[idx]
                    
                active = [x for x in next_rem if x > 0]
                if not active:
                    continue
                    
                step = min(active)
                new_t = t + step
                if new_t > current_goal:
                    continue
                    
                post_drain_rem = tuple(max(0, x - step) if x > 0 else 0 for x in next_rem)
                current_action = list(flip_indices) if first_action is None else first_action
                
                queue.append((post_drain_rem, flips + len(flip_indices), new_t, seq_idx, current_action))

    if optimal_first_action is not None:
        return [labels[i] for i in optimal_first_action]
    return None

import json

# =====================================================================
# 2. GAME LEVEL REGISTRATION (DYNAMIC UNIFIED LOADER)
# =====================================================================

st.sidebar.title("🎮 Engine Control Panel")

# 1. CORE MODALITY SELECTOR
game_mode = st.sidebar.selectbox(
    "Select Game Mode:",
    ["Single-Target Standard", "Multi-Target Sequential Chain"],
    key="global_game_mode_selector"
)

# Hardcoded text definitions mapping to your exact dictionary markers
SINGLE_TARGET_LABELS = {
    1: "Rank 1: The Linear Tutorial",
    2: "Rank 2: One Midflip",
    3: "Rank 3: Two Midflips",
    4: "Rank 4: One Midflip, Three Glasses",
    5: "Rank 5: Two Midflips, Three Glasses",
    6: "Rank 6: Three Midflips, Three Glasses",
    7: "Rank 7: Synergistic Two Midflips",
    8: "Rank 8: Synergistic Three Midflips"
}

MULTI_TARGET_LABELS = {
    1: "Rank 1: Zero Midflip",
    2: "Rank 2: One Midflip",
    3: "Rank 3: Two Midflips",
    4: "Rank 4: Three Midflips"
}

# Determine active labels and file strings based on mode selection
if game_mode == "Single-Target Standard":
    active_labels = SINGLE_TARGET_LABELS
    active_file = "all_hourglass_puzzles.txt"
else:
    active_labels = MULTI_TARGET_LABELS
    active_file = "multitarget_puzzles.txt"
# Hardcoded definitions matching your exact generation keys
RANK_LABELS = {
    1: "Rank 1: The Linear Tutorial",
    2: "Rank 2: One Midflip",
    3: "Rank 3: Two Midflips",
    4: "Rank 4: One Midflip, Three Glasses",
    5: "Rank 5: Two Midflips, Three Glasses",
    6: "Rank 6: Three Midflips, Three Glasses",
    7: "Rank 7: Synergistic Two Midflips",
    8: "Rank 8: Synergistic Three Midflips"
}

# Sidebar Selectbox for picking the exact Rank category
st.sidebar.subheader("Puzzle Difficulty Filter")
selected_rank_id = st.sidebar.selectbox(
    "Choose Rank Classification:",
    options=list(active_labels.keys()),
    format_func=lambda x: active_labels[x],
    key=f"rank_selector_widget_{game_mode}"
)

# 3. PARSE FILE AND INGEST MATCHING LAYOUT RECORDS
LEVELS = []
try:
    with open(active_file, "r", encoding="utf-8") as f:
        level_counter = 1
        for line in f:
            cleaned = line.strip()
            if not cleaned:
                continue
                
            data = json.loads(cleaned)
            
            if data["rank"] == selected_rank_id:
                sizes_list, target_data, par_flips = data["config"]
                
                if isinstance(target_data, list):
                    target_display_str = " ➔ ".join(f"{t}m" for t in target_data)
                else:
                    target_display_str = f"{target_data}m"
                    
                LEVELS.append({
                    "name": f"Level {level_counter}: Glasses {tuple(sizes_list)} → Goal: {target_display_str}",
                    "config": (tuple(sizes_list), target_data, par_flips),
                    "rank_name": data["rank_name"]
                })
                level_counter += 1
except FileNotFoundError:
    if game_mode == "Single-Target Standard":
        LEVELS = [{"name": "Fallback Standard", "config": ((4, 7), 9, 4), "rank_name": "Rank 1: Tutorial"}]
    else:
        LEVELS = [{"name": "Fallback Sequential", "config": ((21, 24, 29), [30, 33, 38], 15), "rank_name": "Rank 4: Three Midflips"}]


# =====================================================================
# 3. STREAMLIT INITIALIZATION & ENGINE STATE
# =====================================================================


# Handle tracking state resets when changing modes or difficulties
mode_and_rank_state_hash = f"{game_mode}_{selected_rank_id}"
if "last_state_hash" not in st.session_state or st.session_state.last_state_hash != mode_and_rank_state_hash:
    st.session_state.current_level_idx = 0
    st.session_state.last_state_hash = mode_and_rank_state_hash

# 4. SINGLE LEVEL SELECTOR DROPDOWN
# 4. SINGLE LEVEL SELECTOR DROPDOWN
level_names = [lvl["name"] for lvl in LEVELS]

# Guard rails to prevent index out of bounds exceptions on quick data swaps
if "current_level_idx" not in st.session_state or st.session_state.current_level_idx >= len(level_names):
    st.session_state.current_level_idx = 0

# Initialize an independent random version seed to trigger key destruction on click
if "random_seed_key_modifier" not in st.session_state:
    st.session_state.random_seed_key_modifier = 0

# 🚀 SOLUTION: The widget key appends the seed modifier. If the modifier changes, the selectbox is rebuilt!
dropdown_key = f"main_level_box_{mode_and_rank_state_hash}_{st.session_state.random_seed_key_modifier}"

selected_level_name = st.sidebar.selectbox(
    "Choose Level Profile:",
    options=level_names,
    index=st.session_state.current_level_idx,
    key=dropdown_key
)

# Detect if the user manually changed the dropdown choice with their mouse cursor
manual_selected_idx = level_names.index(selected_level_name)
if manual_selected_idx != st.session_state.current_level_idx:
    st.session_state.current_level_idx = manual_selected_idx
    st.rerun()

# 5. INLINE RANDOM LEVEL GENERATOR BUTTON (FORCES KEY MUTATION RERUN)
if st.sidebar.button("🔀 Pick Random Level from Rank", key=f"fixed_random_btn_trigger_{mode_and_rank_state_hash}"):
    if len(LEVELS) > 1:
        current = st.session_state.current_level_idx
        valid_indices = [i for i in range(len(LEVELS)) if i != current]
        
        # 1. Update the index pointer variable
        st.session_state.current_level_idx = random.choice(valid_indices)
        
        # 2. Increment the seed modifier to force the selectbox to discard its cache memory and redraw!
        st.session_state.random_seed_key_modifier += 1
    else:
        st.session_state.current_level_idx = 0
            
    # Safely force an instant screen refresh from the main thread flow
    st.rerun()


# Extract core layout elements
lvl_idx = st.session_state.current_level_idx
active_level = LEVELS[lvl_idx]
sizes, raw_target, min_flips_allowed = active_level["config"]
current_sub_rank_title = active_level["rank_name"]

# Handle active target parsing
if isinstance(raw_target, list):
    if "active_target_idx" not in st.session_state or st.session_state.get("active_hash") != mode_and_rank_state_hash:
        st.session_state.active_target_idx = 0
        st.session_state.active_hash = mode_and_rank_state_hash
    active_checkpoint_goal = raw_target[st.session_state.active_target_idx]
    target = active_checkpoint_goal  # Set target variable for hint engine integration
else:
    active_checkpoint_goal = raw_target
    target = raw_target


st.set_page_config(page_title="Hourglass Dynamic Engine", page_icon="⏳", layout="wide")
st.title("⏳ Dynamic Hourglass Puzzle Engine")
st.markdown(f"### Target Complexity: `{current_sub_rank_title}`")
# Track persistent session state matrices

# Build custom state key combined with step parameters
combined_state_init_key = f"{mode_and_rank_state_hash}_{lvl_idx}"
if "time_elapsed" not in st.session_state or "initialized_level" not in st.session_state or st.session_state.initialized_level != st.session_state.current_level_idx:
    st.session_state.initialized_level = st.session_state.current_level_idx
    st.session_state.time_elapsed = 0
    st.session_state.user_flips = 0
    st.session_state.game_active = True
    st.session_state.active_hint = None
    st.session_state.logs = ["System synchronized. All sand settled in lower vessels."]
    st.session_state.active_target_idx = 0
    st.session_state.staged_flips = set()
    st.session_state.move_history = []
    
    st.session_state.glasses = {}
    for i, size in enumerate(sizes):
        label = f"{size}m"
        if label in st.session_state.glasses:
            label = f"{size}m (Index {i})"
        st.session_state.glasses[label] = {"size": size, "top": 0, "bottom": size}
# Render active checkboxes sequentially if playing Multi-Target Mode
if isinstance(raw_target, list):
    checkpoint_indicators = []
    for step_idx, t_val in enumerate(raw_target):
        if step_idx < st.session_state.active_target_idx:
            checkpoint_indicators.append(f"✅ ~~{t_val}m~~")
        elif step_idx == st.session_state.active_target_idx:
            checkpoint_indicators.append(f"🎯 **{t_val}m (Active)**")
        else:
            checkpoint_indicators.append(f"🔒 {t_val}m")
    st.markdown(f"**Chrono Timeline Goals:** {' ➔ '.join(checkpoint_indicators)}")

def reset_engine():
    st.session_state.time_elapsed = 0
    st.session_state.user_flips = 0
    st.session_state.game_active = True
    st.session_state.staged_flips.clear()
    st.session_state.active_hint = None
    st.session_state.logs = ["Engine state reset. Timers synchronized."]
    st.session_state.active_target_idx = 0
    st.session_state.move_history = []
    for label, g in st.session_state.glasses.items():
        g["top"] = 0
        g["bottom"] = g["size"]

# =====================================================================
# 4. INTERACTION BUSINESS LOGIC
# =====================================================================
def toggle_stage_flip(label):
    if not st.session_state.game_active:
        return
    if label in st.session_state.staged_flips:
        st.session_state.staged_flips.remove(label)
    else:
        st.session_state.staged_flips.add(label)

def generate_hint():
    """Calculates the exit route based on the current live board metrics."""
    sizes_list = []
    current_top_sands = []
    
    for label, data in st.session_state.glasses.items():
        sizes_list.append(data["size"])
        current_top_sands.append(data["top"])
    
    # Check if we are running in Multi-Target mode
    if isinstance(raw_target, list):
        # Slice the sequence array to pass only the REMAINING targets to the solver
        remaining_sequence = tuple(raw_target[st.session_state.active_target_idx:])
        
        # Call a specialized multi-target sequential pathfinder
        next_flips = find_next_best_multitarget_step(
            current_state=tuple(current_top_sands),
            sizes=tuple(sizes_list),
            target_sequence=remaining_sequence,
            current_time=st.session_state.time_elapsed
        )
    else:
        # Standard Single-Target calculation loop
        next_flips = find_next_best_step(
            current_state=tuple(current_top_sands),
            sizes=sizes_list,
            target=target,
            current_time=st.session_state.time_elapsed
        )
    
    if next_flips is None:
        st.session_state.active_hint = "⚠️ Mathematically impossible from this state. You should reset!"
    elif len(next_flips) == 0:
        st.session_state.active_hint = "💡 Just click 'Submit Turn Actions' without staging any flips right now."
    else:
        st.session_state.active_hint = f"💡 Optimal path requires flipping: {', '.join(next_flips)} then submitting your turn."

def submit_turn_actions():
    if not st.session_state.game_active:
        return

    current_glasses_snapshot = {
        label: {"size": data["size"], "top": data["top"], "bottom": data["bottom"]}
        for label, data in st.session_state.glasses.items()
    }
    
    snapshot_record = {
        "glasses": current_glasses_snapshot,
        "time_elapsed": st.session_state.time_elapsed,
        "user_flips": st.session_state.user_flips,
        "active_target_idx": st.session_state.active_target_idx,
        "logs": list(st.session_state.logs) # Creates an independent text array clone
    }
    st.session_state.move_history.append(snapshot_record)

    # 1. Process all staged flips at once on a single log row
    flips_executed = list(st.session_state.staged_flips)
    if flips_executed:
        for label in flips_executed:
            g = st.session_state.glasses[label]
            g["top"], g["bottom"] = g["bottom"], g["top"]
            
        st.session_state.user_flips += len(flips_executed)
        glasses_string = " and ".join(flips_executed)
        st.session_state.logs.append(
            f"🔄 Simultaneous Flip: Managed [{glasses_string}] (Total Flips: {st.session_state.user_flips})"
        )
        st.session_state.staged_flips.clear()

    # 2. Advance time to the next logical event boundary
    active_steps = [g["top"] for g in st.session_state.glasses.values() if g["top"] > 0]
    
    if not active_steps:
        st.session_state.logs.append("⚠️ Action Blocked: No active streams are running. Stage a flip first!")
        return
        
    step = min(active_steps)
    st.session_state.time_elapsed += step
    
    for label, g in st.session_state.glasses.items():
        if g["top"] > 0:
            g["top"] -= step
            g["bottom"] += step
            
    st.session_state.logs.append(f"⏩ Advanced +{step}m to event boundary (Total time: {st.session_state.time_elapsed}m)")
    st.session_state.active_hint = None  # Clear visual hint on grid change
    
    # 3. Process endgame boundary evaluations
    # 3. ADDED CHANGE: MULTI-TARGET SEQUENCE VS STANDARD EVALUATION METRICS
    if isinstance(raw_target, list):
        # Multi-Target Evaluation Routing Matrix
        if st.session_state.time_elapsed == active_checkpoint_goal:
            if st.session_state.active_target_idx < len(raw_target) - 1:
                st.session_state.logs.append(f"✨ Milestone Secured! Successfully hit checkpoint {active_checkpoint_goal}m! Continuing tracking...")
                st.session_state.active_target_idx += 1
                #st.rerun() 
            else:
                st.session_state.game_active = False
                if st.session_state.user_flips <= min_flips_allowed:
                    st.session_state.logs.append(f"🎉 Perfect Sequence Clear! Cleared all goals in {st.session_state.user_flips} flips (Par: {min_flips_allowed}).")
                else:
                    st.session_state.logs.append(f"⚠️ Chain Secured but Inefficient! Optimal solution can be done in {min_flips_allowed} flips.")
                    
        elif st.session_state.time_elapsed > active_checkpoint_goal:
            st.session_state.game_active = False
            st.session_state.logs.append(f"❌ Target Overshot! You reached {st.session_state.time_elapsed}m, passing active target threshold {active_checkpoint_goal}m.")
    else:
        # Standard single target checking routing rules
        if st.session_state.time_elapsed == target:
            st.session_state.game_active = False
            if st.session_state.user_flips <= min_flips_allowed:
                st.session_state.logs.append(f"🎉 Perfect Win! Hit exactly {target}m in {st.session_state.user_flips} flips.")
            else:
                st.session_state.logs.append(f"⚠️ Target Met, but Inefficient! Optimal path can be done in {min_flips_allowed} flips.")
        elif st.session_state.time_elapsed > target:
            st.session_state.game_active = False
            st.session_state.logs.append(f"❌ Target Overshot! You reached {st.session_state.time_elapsed}m, passing your goal of {target}m.")

def execute_undo_move():
    """Pops the last layout snapshot state entry and re-applies it back onto active keys."""
    if not st.session_state.move_history:
        return
        
    # Extract the last written historical state row entry
    previous_state = st.session_state.move_history.pop()
    
    # Re-apply tracking variables
    st.session_state.glasses = previous_state["glasses"]
    st.session_state.time_elapsed = previous_state["time_elapsed"]
    st.session_state.user_flips = previous_state["user_flips"]
    st.session_state.active_target_idx = previous_state["active_target_idx"]
    st.session_state.logs = previous_state["logs"]
    
    # Automatically wake up game active parameters in case they undo out of an overshot loss state
    st.session_state.game_active = True
    st.session_state.active_hint = None
    st.session_state.staged_flips.clear()

# =====================================================================
# 5. GRAPHICAL DESKTOP RENDER VIEWPORT
# =====================================================================
with st.sidebar: 
    st.markdown("---")
    st.markdown("### Level Constraints")
    st.markdown(f"**Target Goal:** `{target} min`")
    st.markdown(f"**Min Flip Limit:** `{min_flips_allowed} flips`")
    st.button("⏪ Undo Last Move", on_click=execute_undo_move, disabled=len(st.session_state.move_history) == 0, use_container_width=True)
    st.button("🔄 Reset Active Level", on_click=reset_engine, disabled=len(st.session_state.move_history) == 0, use_container_width=True)

    st.markdown("---")
    st.markdown("### Puzzle Assistance")
    st.button("💡 Request Next Best Action", on_click=generate_hint, disabled=not st.session_state.game_active, use_container_width=True)
    
    if st.session_state.active_hint:
        if "⚠️" in st.session_state.active_hint:
            st.error(st.session_state.active_hint)
        else:
            st.info(st.session_state.active_hint)

# Main Stats Dashboard Row
col_elapsed, col_flips, col_target = st.columns(3)
with col_elapsed:
    st.metric(label="Elapsed Game Time", value=f"{st.session_state.time_elapsed} min")
with col_flips:
    st.metric(label="Total Actions Spent", value=f"{st.session_state.user_flips} flips")
with col_target:
    st.metric(label="Target Objective", value=f"{active_checkpoint_goal} min")
st.markdown("---")
num_glasses = len(st.session_state.glasses)
columns = st.columns(num_glasses)
for idx, (label, g) in enumerate(st.session_state.glasses.items()):
    with columns[idx]:
        is_staged = label in st.session_state.staged_flips# Calculate visual staging inversion swaps
        disp_top = g["bottom"] if is_staged else g["top"]
        disp_bottom = g["top"] if is_staged else g["bottom"]
        if is_staged:
            st.markdown(f"### {label} Vessel 🔄 STAGED")
        else:
            st.markdown(f"### {label} Vessel")
        st.text(f"▼ Top:    [{'█' * disp_top}{' ' * (g['size'] - disp_top)}] {disp_top}m")
        st.text("    ⏳ ======= ⏳")
        st.text(f"▲ Bottom: [{'█' * disp_bottom}{' ' * (g['size'] - disp_bottom)}] {disp_bottom}m")
        st.button(
            "Unstage Flip" if is_staged else "Stage Flip 🔄",
            key=f"btn_{idx}",on_click=toggle_stage_flip,args=(label,),
            disabled=not st.session_state.game_active,use_container_width=True,
            type="secondary" if is_staged else "primary")
        
st.markdown("---")
st.button("🚀 Submit Turn Actions & Step Forward",key=f"global_submit_turn_action_button",on_click=submit_turn_actions,
disabled=not st.session_state.game_active,use_container_width=True,type="primary")
st.subheader("Chronological Event Log")
with st.container(border=True):
    for entry in reversed(st.session_state.logs):
        if "🎉" in entry:st.success(entry)
        elif "❌" in entry:st.error(entry)
        elif "⚠️" in entry:st.warning(entry)
        else:st.code(entry, language="text")
