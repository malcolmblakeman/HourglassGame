import streamlit as st
import itertools
from collections import deque
import random
import json

# =====================================================================
# GLOBAL CONSTANTS
# =====================================================================
GLASSES_PER_CHANNEL = 2  # Each channel always has exactly 2 hourglasses

CHANNEL_NAMES = ["Alpha", "Beta", "Gamma", "Delta", "Epsilon", "Zeta"]
CHANNEL_COLORS = {
    "Alpha": "#e74c3c",
    "Beta": "#3498db",
    "Gamma": "#27ae60",
    "Delta": "#8e44ad",
    "Epsilon": "#e67e22",
    "Zeta": "#16a085",
}
CHANNEL_ICONS = {
    "Alpha": "🔴",
    "Beta": "🔵",
    "Gamma": "🟢",
    "Delta": "🟣",
    "Epsilon": "🟠",
    "Zeta": "🟤",
}

def hex_to_rgb(hex_color):
    """Convert hex color string to (r, g, b) integer tuple."""
    h = hex_color.lstrip('#')
    return tuple(int(h[i:i+2], 16) for i in (0, 2, 4))

CHANNEL_RGB = {name: hex_to_rgb(color) for name, color in CHANNEL_COLORS.items()}


# =====================================================================
# 1. CORE PATHFINDING SOLVERS (BFS ENGINES)
# =====================================================================

def find_next_best_step(current_state, sizes, target, current_time, labels=None):
    """
    Standard Single-Target BFS solver from current mid-game state.
    """
    n = len(sizes)
    if labels is None:
        labels = [f"{s}m" for s in sizes]

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
                current_action = list(flip_indices) if first_action is None else first_action

                queue.append((post_drain_rem, flips + len(flip_indices), new_t, current_action))

    if optimal_first_action is not None:
        return [labels[i] for i in optimal_first_action]
    return None


def find_next_best_multitarget_step(current_state, sizes, target_sequence, current_time, labels=None):
    """
    Multi-Target Sequential Chain BFS solver from current mid-game state.
    """
    n = len(sizes)
    if labels is None:
        labels = [f"{s}m" for s in sizes]

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


def find_next_best_convergence_step(current_state, sizes, target, current_time, num_channels, labels=None):
    """
    N-Channel Convergence BFS solver from the CURRENT live game state.
    - ALL channels must have running streams continuously.
    - Last step (hitting target) must:
        - Have exactly 1 flip.
        - That single glass flipped must not have been empty before flipping.
        - ALL channels must end at the exact same time (all channel mins are equal).
    - Note: Midflips are NOT counted or enforced during live hinting.
    """
    n = len(sizes)
    glasses_per_channel = n // num_channels

    # Build channel index groups: [[0,1], [2,3], [4,5], ...]
    channel_index_groups = [
        list(range(c * glasses_per_channel, (c + 1) * glasses_per_channel))
        for c in range(num_channels)
    ]

    if labels is None:
        labels = []
        for i, s in enumerate(sizes):
            ch_idx = i // glasses_per_channel
            ch_name = CHANNEL_NAMES[ch_idx]
            labels.append(f"{ch_name}-{s}m")

    # Queue layout: (current_rem, current_time, flips_count, first_action)
    initial_state = (current_state, current_time, 0, None)
    queue = deque([initial_state])
    visited = {}

    best_flips = float('inf')
    optimal_first_action = None

    while queue:
        rem, t, flips, first_action = queue.popleft()

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

        # Try all combinations of flips
        for r in range(n + 1):
            for flip_indices in itertools.combinations(range(n), r):
                next_rem = list(rem)

                # Flip glasses
                for idx in flip_indices:
                    next_rem[idx] = sizes[idx] - next_rem[idx]

                # Check active sand in ALL channels
                channel_mins = []
                valid_step = True
                for c_indices in channel_index_groups:
                    active_in_channel = [next_rem[i] for i in c_indices if next_rem[i] > 0]
                    if not active_in_channel:
                        valid_step = False
                        break
                    channel_mins.append(min(active_in_channel))

                if not valid_step:
                    continue  # Invalid: at least one channel has no flowing sand

                step = min(channel_mins)
                new_t = t + step

                if new_t > target:
                    continue

                # Last step convergence constraints
                if new_t == target:
                    # 1. Last step must have exactly 1 flip
                    if len(flip_indices) != 1:
                        continue
                    flipped_idx = flip_indices[0]
                    # 2. The single glass flipped cannot be empty before flip
                    if rem[flipped_idx] == 0:
                        continue
                    # 3. ALL channels must end at the same time
                    if len(set(channel_mins)) != 1:
                        continue

                post_drain_rem = tuple(max(0, x - step) if x > 0 else 0 for x in next_rem)
                current_action = list(flip_indices) if first_action is None else first_action

                queue.append((post_drain_rem, new_t, flips + len(flip_indices), current_action))

    if optimal_first_action is not None:
        return [labels[i] for i in optimal_first_action]
    return None


# =====================================================================
# 2. STREAMLIT APP INITIALIZATION
# =====================================================================
st.set_page_config(page_title="Hourglass Game", page_icon="⏳", layout="wide")

st.markdown("""
<style>
html, body {
    overflow-y: scroll !important;
    overflow-x: hidden !important;
    height: auto !important;
    min-height: 100%;
}

html{
        zoom: 80%;
    }

/* Main app container */
.stApp {
    overflow-y: auto !important;
    overflow-x: hidden !important;
    height: auto !important;
    min-height: 100vh !important;
}

/* Main content */
[data-testid="stAppViewContainer"] {
    overflow-y: auto !important;
    height: auto !important;
}

[data-testid="stMain"] {
    overflow-y: auto !important;
    height: auto !important;
}

section[data-testid="stSidebar"] {
    overflow-y: auto !important;
}

/* Content wrapper */
.block-container {
    padding-top: 2rem !important;
    padding-bottom: 5rem !important;
    max-width: 100% !important;
}

/* Prevent horizontal scrolling */
html, body, .stApp {
    overflow-x: hidden !important;
}
</style>
""", unsafe_allow_html=True)

st.header("⏳ Hourglass Game")

# =====================================================================
# 3. SIDEBAR NAVIGATION & PUZZLE LOADER WITH BULLETPROOF FALLBACKS
# =====================================================================
st.sidebar.subheader("🎮 Engine Control Panel")

game_mode = st.sidebar.selectbox(
    "Select Game Mode:",
    ["Single-Target Standard", "Multi-Target Sequential Chain", "Parallel Channel Convergence"],
    key="global_game_mode_selector"
)

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

CONVERGENCE_LABELS = {
    1: "Rank 1: Two Channels",
    2: "Rank 2: Three Channels",
}

if game_mode == "Single-Target Standard":
    active_labels = SINGLE_TARGET_LABELS
    active_file = "all_hourglass_puzzles.txt"
elif game_mode == "Multi-Target Sequential Chain":
    active_labels = MULTI_TARGET_LABELS
    active_file = "multitarget_puzzles.txt"
else:
    active_labels = CONVERGENCE_LABELS
    active_file = "convergence_puzzles.txt"

st.sidebar.subheader("Puzzle Difficulty Filter")
selected_rank_id = st.sidebar.selectbox(
    "Choose Rank Classification:",
    options=list(active_labels.keys()),
    format_func=lambda x: active_labels[x],
    key=f"rank_selector_widget_{game_mode}"
)

# Robust verified math-presets used if file read fails or has no matches
FALLBACK_LEVELS = {
    "Single-Target Standard": {
        1: [{"name": "Standard Rank 1 (Fallback): Glasses (4, 7) → Goal: 9m", "config": ((4, 7), 9, 4), "rank_name": "Rank 1: The Linear Tutorial"}],
        2: [{"name": "Standard Rank 2 (Fallback): Glasses (5, 8) → Goal: 11m", "config": ((5, 8), 11, 4), "rank_name": "Rank 2: One Midflip"}],
        3: [{"name": "Standard Rank 3 (Fallback): Glasses (3, 7) → Goal: 10m", "config": ((3, 7), 10, 5), "rank_name": "Rank 3: Two Midflips"}],
        4: [{"name": "Standard Rank 4 (Fallback): Glasses (3, 5, 8) → Goal: 12m", "config": ((3, 5, 8), 12, 5), "rank_name": "Rank 4: One Midflip, Three Glasses"}],
        5: [{"name": "Standard Rank 5 (Fallback): Glasses (4, 7, 9) → Goal: 15m", "config": ((4, 7, 9), 15, 6), "rank_name": "Rank 5: Two Midflips, Three Glasses"}],
        6: [{"name": "Standard Rank 6 (Fallback): Glasses (5, 8, 11) → Goal: 17m", "config": ((5, 8, 11), 17, 7), "rank_name": "Rank 6: Three Midflips, Three Glasses"}],
        7: [{"name": "Standard Rank 7 (Fallback): Glasses (3, 7, 10) → Goal: 14m", "config": ((3, 7, 10), 14, 6), "rank_name": "Rank 7: Synergistic Two Midflips"}],
        8: [{"name": "Standard Rank 8 (Fallback): Glasses (4, 9, 11) → Goal: 19m", "config": ((4, 9, 11), 19, 8), "rank_name": "Rank 8: Synergistic Three Midflips"}],
    },
    "Multi-Target Sequential Chain": {
        1: [{"name": "Sequential Rank 1 (Fallback): Glasses (3, 7) → Goal: 3 ➔ 7", "config": ((3, 7), [3, 7], 2), "rank_name": "Rank 1: Zero Midflip"}],
        2: [{"name": "Sequential Rank 2 (Fallback): Glasses (3, 5, 7) → Goal: 8 ➔ 11", "config": ((3, 5, 7), [8, 11], 4), "rank_name": "Rank 2: One Midflip"}],
        3: [{"name": "Sequential Rank 3 (Fallback): Glasses (4, 7, 9) → Goal: 11 ➔ 15", "config": ((4, 7, 9), [11, 15], 6), "rank_name": "Rank 3: Two Midflips"}],
        4: [{"name": "Sequential Rank 4 (Fallback): Glasses (21, 24, 29) → Goal: 30 ➔ 33 ➔ 38", "config": ((21, 24, 29), [30, 33, 38], 15), "rank_name": "Rank 4: Three Midflips"}],
    },
    "Parallel Channel Convergence": {
        1: [
            {"name": "Convergence L1 (Fallback): Alpha (4, 6) | Beta (3, 5) → Goal: 9m", "config": ((4, 6, 3, 5), 9, 5), "rank_name": "Rank 1: Two Channels"},
            {"name": "Convergence L2 (Fallback): Alpha (5, 7) | Beta (4, 9) → Goal: 11m", "config": ((5, 7, 4, 9), 11, 6), "rank_name": "Rank 1: Two Channels"}
        ],
        2: [
            {"name": "Convergence L4 (Fallback): Alpha (4, 6) | Beta (3, 5) | Gamma (2, 7) → Goal: 11m", "config": ((4, 6, 3, 5, 2, 7), 11, 6), "rank_name": "Rank 3: Three Channels"},
            {"name": "Convergence L5 (Fallback): Alpha (5, 7) | Beta (3, 8) | Gamma (4, 6) → Goal: 13m", "config": ((5, 7, 3, 8, 4, 6), 13, 7), "rank_name": "Rank 3: Three Channels"},
            {"name": "Convergence L6 (Fallback): Alpha (5, 7) | Beta (3, 8) | Gamma (4, 6) → Goal: 13m", "config": ((6, 8, 7, 12, 13, 14), 17, 11), "rank_name": "Rank 3: Three Channels"},
            {"name": "Convergence L7 (Fallback): Alpha (5, 7) | Beta (3, 8) | Gamma (4, 6) → Goal: 13m", "config": ((6, 17, 8, 14, 12, 15), 19, 12), "rank_name": "Rank 3: Three Channels"},  
        #6, 17, 8, 14, 12, 15], 19
        ],
    }
}

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

                # Build dynamic channel display for convergence
                if game_mode == "Parallel Channel Convergence":
                    nc = len(sizes_list) // GLASSES_PER_CHANNEL
                    ch_names = CHANNEL_NAMES[:nc]
                    channel_strs = []
                    for ci in range(nc):
                        ch_glasses = sizes_list[ci * GLASSES_PER_CHANNEL:(ci + 1) * GLASSES_PER_CHANNEL]
                        channel_strs.append(f"{ch_names[ci]} {tuple(ch_glasses)}")
                    level_desc = f"Level {level_counter}: {' | '.join(channel_strs)} → Goal: {target_display_str}"
                else:
                    level_desc = f"Level {level_counter}: Glasses {tuple(sizes_list)} → Goal: {target_display_str}"

                LEVELS.append({
                    "name": level_desc,
                    "config": (tuple(sizes_list), target_data, par_flips),
                    "rank_name": data["rank_name"]
                })
                level_counter += 1
except Exception:
    pass

# Force robust fallback if empty
if not LEVELS:
    LEVELS = FALLBACK_LEVELS[game_mode].get(selected_rank_id, FALLBACK_LEVELS[game_mode][1])

# State hashes to handle index changing safely
mode_and_rank_state_hash = f"{game_mode}_{selected_rank_id}"
if "last_state_hash" not in st.session_state:
    st.session_state.current_level_idx = 0
    st.session_state.last_state_hash = mode_and_rank_state_hash

level_names = [lvl["name"] for lvl in LEVELS]

# Detect if the game mode or rank classification just changed
if "last_state_hash" not in st.session_state or st.session_state.last_state_hash != mode_and_rank_state_hash:
    st.session_state.last_state_hash = mode_and_rank_state_hash

    # NEW LOGIC: Instantly pick a random level instead of defaulting to 0
    if len(LEVELS) > 1:
        current = st.session_state.current_level_idx
        valid_indices = [i for i in range(len(LEVELS)) if i != current]
        st.session_state.current_level_idx = random.choice(valid_indices)
        st.session_state.random_seed_key_modifier += 1
    else:
        st.session_state.current_level_idx = 0
    st.rerun()

if "current_level_idx" not in st.session_state or st.session_state.current_level_idx >= len(level_names):
    st.session_state.current_level_idx = 0

if "random_seed_key_modifier" not in st.session_state:
    st.session_state.random_seed_key_modifier = 0

dropdown_key = f"main_level_box_{mode_and_rank_state_hash}_{st.session_state.random_seed_key_modifier}"
selected_level_name = st.sidebar.selectbox(
    "Choose Level Profile:",
    options=level_names,
    index=st.session_state.current_level_idx,
    key=dropdown_key
)

manual_selected_idx = level_names.index(selected_level_name)
if manual_selected_idx != st.session_state.current_level_idx:
    st.session_state.current_level_idx = manual_selected_idx
    st.rerun()

if st.sidebar.button("🔀 Pick Random Level", key=f"fixed_random_btn_trigger_{mode_and_rank_state_hash}"):
    if len(LEVELS) > 1:
        current = st.session_state.current_level_idx
        valid_indices = [i for i in range(len(LEVELS)) if i != current]
        st.session_state.current_level_idx = random.choice(valid_indices)
        st.session_state.random_seed_key_modifier += 1
    else:
        st.session_state.current_level_idx = 0
    st.rerun()

lvl_idx = st.session_state.current_level_idx
active_level = LEVELS[lvl_idx]
sizes, raw_target, min_flips_allowed = active_level["config"]
current_sub_rank_title = active_level["rank_name"]

# Parse channel parameters dynamically for convergence mode
if game_mode == "Parallel Channel Convergence":
    n_total = len(sizes)
    num_channels = n_total // GLASSES_PER_CHANNEL
    active_channel_names = CHANNEL_NAMES[:num_channels]
else:
    active_channel_names = []
    num_channels = 0

# Parse sequential objectives
if isinstance(raw_target, list):
    if "active_target_idx" not in st.session_state or st.session_state.get("active_hash") != mode_and_rank_state_hash:
        st.session_state.active_target_idx = 0
        st.session_state.active_hash = mode_and_rank_state_hash
    active_checkpoint_goal = raw_target[st.session_state.active_target_idx]
    target = active_checkpoint_goal
else:
    active_checkpoint_goal = raw_target
    target = raw_target

st.markdown(f"### Target Complexity: `{current_sub_rank_title}`")

# =====================================================================
# 4. SESSION STATE REGISTRY (BOARD LAYOUTS)
# =====================================================================
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

    flat_sizes = list(sizes)
    temp_glasses = {}
    for i, size in enumerate(flat_sizes):
        if game_mode == "Parallel Channel Convergence":
            channel_idx = i // GLASSES_PER_CHANNEL
            channel = CHANNEL_NAMES[channel_idx]
            base_label = f"{channel}-{size}m"
        else:
            channel = "Standard"
            base_label = f"{size}m"

        label = base_label
        suffix = 2
        while label in temp_glasses:
            if game_mode == "Parallel Channel Convergence":
                label = f"{base_label}#{suffix}"
            else:
                label = f"{base_label} ({i})"
            suffix += 1

        temp_glasses[label] = {
            "size": size,
            "top": 0,
            "bottom": size,
            "channel": channel,
            "idx": i
        }
    st.session_state.glasses = temp_glasses

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
# 5. USER INTERACTIONS & TURN SUBMISSION
# =====================================================================
def toggle_stage_flip(label):
    if not st.session_state.game_active:
        return
    if label in st.session_state.staged_flips:
        st.session_state.staged_flips.remove(label)
    else:
        st.session_state.staged_flips.add(label)

def generate_hint():
    sizes_list = []
    current_top_sands = []
    labels_list = []
    for label, data in st.session_state.glasses.items():
        sizes_list.append(data["size"])
        current_top_sands.append(data["top"])
        labels_list.append(label)

    if game_mode == "Parallel Channel Convergence":
        next_flips = find_next_best_convergence_step(
            tuple(current_top_sands),
            tuple(sizes_list),
            target,
            st.session_state.time_elapsed,
            num_channels,
            labels=labels_list
        )
    elif isinstance(raw_target, list):
        remaining_sequence = tuple(raw_target[st.session_state.active_target_idx:])
        next_flips = find_next_best_multitarget_step(
            current_state=tuple(current_top_sands),
            sizes=tuple(sizes_list),
            target_sequence=remaining_sequence,
            current_time=st.session_state.time_elapsed,
            labels=labels_list
        )
    else:
        next_flips = find_next_best_step(
            current_state=tuple(current_top_sands),
            sizes=sizes_list,
            target=target,
            current_time=st.session_state.time_elapsed,
            labels=labels_list
        )

    if next_flips is None:
        st.session_state.active_hint = "⚠️ Mathematically impossible from this state under strict rules. You should reset/undo!"
    elif len(next_flips) == 0:
        st.session_state.active_hint = "💡 Just click 'Submit Turn Actions' without staging any flips right now."
    else:
        st.session_state.active_hint = f"💡 Optimal path requires flipping: {', '.join(next_flips)} then submitting your turn."

def submit_turn_actions():
    if not st.session_state.game_active:
        return

    # Take Snapshot for UNDO pipeline
    current_glasses_snapshot = {
        label: {"size": data["size"], "top": data["top"], "bottom": data["bottom"],
                "channel": data.get("channel", "Standard"), "idx": data.get("idx", 0)}
        for label, data in st.session_state.glasses.items()
    }
    snapshot_record = {
        "glasses": current_glasses_snapshot,
        "time_elapsed": st.session_state.time_elapsed,
        "user_flips": st.session_state.user_flips,
        "active_target_idx": st.session_state.active_target_idx,
        "logs": list(st.session_state.logs)
    }
    st.session_state.move_history.append(snapshot_record)

    # 1. Flip any staged hourglasses
    flips_executed = list(st.session_state.staged_flips)
    is_midflip_action = False

    # Store initial levels before flips to check for empty-flips and midflips
    orig_levels_snapshot = {lbl: g["top"] for lbl, g in st.session_state.glasses.items()}

    if flips_executed:
        for label in flips_executed:
            g = st.session_state.glasses[label]
            if 0 < orig_levels_snapshot[label] < g["size"]:
                is_midflip_action = True
            g["top"], g["bottom"] = g["bottom"], g["top"]

        st.session_state.user_flips += len(flips_executed)
        glasses_string = " + ".join(flips_executed)
        st.session_state.logs.append(
            f"🔄 Flip Action: [{glasses_string}] {'(⭐ MIDFLIP DETECTED!)' if is_midflip_action else ''} (Total flips: {st.session_state.user_flips})"
        )
        st.session_state.staged_flips.clear()

    # 2. Advance time based on game mode constraints
    step = None
    if game_mode == "Parallel Channel Convergence":
        # Collect minimum active sand per channel
        channel_mins = {}
        blocked_channels = []
        for ch_name in active_channel_names:
            active = [gd["top"] for gd in st.session_state.glasses.values() if gd.get("channel") == ch_name and gd["top"] > 0]
            if not active:
                blocked_channels.append(ch_name)
            else:
                channel_mins[ch_name] = min(active)

        if blocked_channels:
            st.session_state.logs.append(f"⚠️ Action Blocked: ALL channels must have active sand streams! Empty channel(s): {', '.join(blocked_channels)}")
            st.session_state.move_history.pop()
            st.session_state.user_flips -= len(flips_executed)
            return

        step = min(channel_mins.values())
    else:
        active_steps = [g["top"] for g in st.session_state.glasses.values() if g["top"] > 0]
        if not active_steps:
            st.session_state.logs.append("⚠️ Action Blocked: No active streams are running. Stage a flip first!")
            st.session_state.move_history.pop()
            return
        step = min(active_steps)

    new_t = st.session_state.time_elapsed + step

    # 3. Apply Strict Convergence Constraints if reaching target
    if game_mode == "Parallel Channel Convergence" and new_t == target:
        # User constraint 1: Exactly 1 flip on the last step
        if len(flips_executed) != 1:
            st.session_state.game_active = False
            st.session_state.logs.append("❌ Invalid Convergence: The last step to reach the goal must have exactly ONE flip!")
        else:
            flipped_label = flips_executed[0]
            # User constraint 2: The single flipped glass cannot have been empty (rem == 0) before the flip
            pre_flip_top = orig_levels_snapshot[flipped_label]
            if pre_flip_top == 0:
                st.session_state.game_active = False
                st.session_state.logs.append(f"❌ Invalid Convergence: The final flipped glass ({flipped_label}) was empty before flipping!")

        # User constraint 3: ALL channels must end at the same time
        if len(set(channel_mins.values())) != 1:
            st.session_state.game_active = False
            detail = " | ".join(f"{ch}={m}m" for ch, m in channel_mins.items())
            st.session_state.logs.append(f"❌ Invalid Convergence: Channels did not end together! {detail}")

    # Apply the physical drain
    st.session_state.time_elapsed = new_t
    for label, g in st.session_state.glasses.items():
        if g["top"] > 0:
            g["top"] -= step
            g["bottom"] += step

    st.session_state.logs.append(f"⏩ Advanced +{step}m (Total: {st.session_state.time_elapsed}m)")
    st.session_state.active_hint = None

    # 4. Evaluation Criteria
    if game_mode == "Parallel Channel Convergence":
        if st.session_state.time_elapsed == target:
            if st.session_state.game_active:
                st.session_state.game_active = False
                ch_list = " + ".join(active_channel_names)
                st.session_state.logs.append(f"🎉 Perfect Sync Clear! All {num_channels} channels ({ch_list}) converged in {st.session_state.user_flips} flips!")
        elif st.session_state.time_elapsed > target:
            st.session_state.game_active = False
            st.session_state.logs.append(f"❌ Target Overshot! Passed goal threshold of {target}m.")

    elif isinstance(raw_target, list):
        if st.session_state.time_elapsed == active_checkpoint_goal:
            if st.session_state.active_target_idx < len(raw_target) - 1:
                st.session_state.logs.append(f"✨ Milestone Secured! Hit checkpoint {active_checkpoint_goal}m! Proceeding...")
                st.session_state.active_target_idx += 1
            else:
                st.session_state.game_active = False
                if st.session_state.user_flips <= min_flips_allowed:
                    st.session_state.logs.append(f"🎉 Perfect Sequence Clear! Cleared all goals in {st.session_state.user_flips} flips (Par: {min_flips_allowed}).")
                else:
                    st.session_state.logs.append(f"⚠️ Chain Secured but Inefficient! Optimal is {min_flips_allowed} flips.")
        elif st.session_state.time_elapsed > active_checkpoint_goal:
            st.session_state.game_active = False
            st.session_state.logs.append(f"❌ Target Overshot! Reached {st.session_state.time_elapsed}m, passing active target threshold {active_checkpoint_goal}m.")
    else:
        if st.session_state.time_elapsed == target:
            st.session_state.game_active = False
            if st.session_state.user_flips <= min_flips_allowed:
                st.session_state.logs.append(f"🎉 Perfect Win! Hit exactly {target}m in {st.session_state.user_flips} flips.")
            else:
                st.session_state.logs.append(f"⚠️ Target Met, but Inefficient! Optimal path: {min_flips_allowed} flips.")
        elif st.session_state.time_elapsed > target:
            st.session_state.game_active = False
            st.session_state.logs.append(f"❌ Target Overshot! Reached {st.session_state.time_elapsed}m, passing your goal of {target}m.")

def execute_undo_move():
    if not st.session_state.move_history:
        return
    previous_state = st.session_state.move_history.pop()
    st.session_state.glasses = previous_state["glasses"]
    st.session_state.time_elapsed = previous_state["time_elapsed"]
    st.session_state.user_flips = previous_state["user_flips"]
    st.session_state.active_target_idx = previous_state["active_target_idx"]
    st.session_state.logs = previous_state["logs"]
    st.session_state.game_active = True
    st.session_state.active_hint = None
    st.session_state.staged_flips.clear()

# =====================================================================
# 6. LAYOUT RENDERING
# =====================================================================

with st.sidebar:
    st.markdown("### Level Constraints")
    st.markdown(f"**Target Goal:** `{target} min`")
    st.markdown(f"**Min Flip Limit:** `{min_flips_allowed} flips`")
    st.button("⏪ Undo Last Move", on_click=execute_undo_move, disabled=len(st.session_state.move_history) == 0, use_container_width=True)
    st.button("🔄 Reset Active Level", on_click=reset_engine, disabled=len(st.session_state.move_history) == 0, use_container_width=True)

    st.markdown("### Puzzle Assistance")
    st.button("💡 Request Next Best Action", on_click=generate_hint, disabled=not st.session_state.game_active, use_container_width=True)
    if st.session_state.active_hint:
        if "⚠️" in st.session_state.active_hint:
            st.error(st.session_state.active_hint)
        else:
            st.info(st.session_state.active_hint)

# Multi-target goals timeline
if game_mode == "Multi-Target Sequential Chain" and isinstance(raw_target, list):
    indicators = [f"✅ {v}m" if i < st.session_state.active_target_idx else f"🎯 {v}m" if i == st.session_state.active_target_idx else f"🔒 {v}m" for i, v in enumerate(raw_target)]
    st.markdown(f"**Chrono Timeline Goals:** {' ➔ '.join(indicators)}")

col_elapsed, col_flips, col_target = st.columns(3)
with col_elapsed:
    st.metric(label="Elapsed Game Time", value=f"{st.session_state.time_elapsed} min")
with col_flips:
    st.metric(label="Total Actions Spent", value=f"{st.session_state.user_flips} flips")
with col_target:
    st.metric(label="Target Objective", value=f"{active_checkpoint_goal} min")

st.markdown("---")

# Render columns — DYNAMIC N-CHANNEL LAYOUT FOR CONVERGENCE
if game_mode == "Parallel Channel Convergence":
    channel_cols = st.columns(num_channels)

    for c_idx, col in enumerate(channel_cols):
        ch_name = active_channel_names[c_idx]
        ch_color = CHANNEL_COLORS[ch_name]
        ch_icon = CHANNEL_ICONS[ch_name]
        cr, cg, cb = CHANNEL_RGB[ch_name]

        channel_items = [(l, g) for l, g in st.session_state.glasses.items() if g.get("channel") == ch_name]

        with col:
            st.markdown(
                f"""
                <div style="background-color: rgba({cr}, {cg}, {cb}, 0.05); padding: 16px; border-radius: 12px; border: 1.5px solid rgba({cr}, {cg}, {cb}, 0.2); border-top: 6px solid {ch_color}; margin-bottom: 20px;">
                    <h3 style="margin: 0; color: {ch_color}; text-align: center; font-size: 1.4rem;">{ch_icon} Channel {ch_name}</h3>
                    <p style="margin: 6px 0 0 0; text-align: center; color: #555; font-size: 0.95rem;">
                        Must always have at least one active running sand stream.
                    </p>
                </div>
                """,
                unsafe_allow_html=True
            )
            if channel_items:
                g_cols = st.columns(len(channel_items))
                for idx, (label, gd) in enumerate(channel_items):
                    with g_cols[idx]:
                        is_staged = label in st.session_state.staged_flips
                        disp_top = gd["bottom"] if is_staged else gd["top"]
                        disp_bottom = gd["top"] if is_staged else gd["bottom"]

                        border_color = ch_color if is_staged else f"rgba({cr}, {cg}, {cb}, 0.15)"
                        staged_badge = f'<span style="background-color: {ch_color}; color: white; font-size: 0.75rem; padding: 2px 6px; border-radius: 4px; margin-left: 6px; font-weight: bold;">STAGED</span>' if is_staged else ''

                        st.markdown(
                            f"""
                            <div style="background-color: rgba({cr}, {cg}, {cb}, 0.02); border: 1.5px solid {border_color}; border-radius: 8px; padding: 12px; text-align: center; margin-bottom: 12px;">
                                <span style="font-weight: bold; color: {ch_color}; font-size: 1.1rem;">{label}</span>
                                {staged_badge}
                            </div>
                            """,
                            unsafe_allow_html=True
                        )

                        st.text(f"▼ Top:    [{'█'*disp_top}{'·'*(gd['size']-disp_top)}] {disp_top}m")
                        st.text("    ⏳ ═══════ ⏳")
                        st.text(f"▲ Bottom: [{'█'*disp_bottom}{'·'*(gd['size']-disp_bottom)}] {disp_bottom}m")
                        st.button(
                            "Unstage" if is_staged else "Stage Flip 🔄",
                            key=f"btn_ch{c_idx}_{label}_{idx}",
                            on_click=toggle_stage_flip,
                            args=(label,),
                            disabled=not st.session_state.game_active,
                            use_container_width=True,
                            type="secondary" if is_staged else "primary"
                        )

else:
    # Standard or Multi-Target rendering layout
    num_glasses = len(st.session_state.glasses)
    columns = st.columns(num_glasses)
    for idx, (label, g) in enumerate(st.session_state.glasses.items()):
        with columns[idx]:
            is_staged = label in st.session_state.staged_flips
            disp_top = g["bottom"] if is_staged else g["top"]
            disp_bottom = g["top"] if is_staged else g["bottom"]
            if is_staged:
                st.markdown(f"### {label} 🔄 STAGED")
            else:
                st.markdown(f"### {label}")
            st.text(f"▼ Top:    [{'█' * disp_top}{' ' * (g['size'] - disp_top)}] {disp_top}m")
            st.text("    ⏳ ======= ⏳")
            st.text(f"▲ Bottom: [{'█' * disp_bottom}{' ' * (g['size'] - disp_bottom)}] {disp_bottom}m")
            st.button(
                "Unstage Flip" if is_staged else "Stage Flip 🔄",
                key=f"btn_std_{label}_{idx}",
                on_click=toggle_stage_flip,
                args=(label,),
                disabled=not st.session_state.game_active,
                use_container_width=True,
                type="secondary" if is_staged else "primary"
            )

st.markdown("---")
st.button("🚀 Submit Turn Actions & Step Forward",
          key="global_submit_turn_action_button",
          on_click=submit_turn_actions,
          disabled=not st.session_state.game_active,
          use_container_width=True,
          type="primary")

st.subheader("Chronological Event Log")
with st.container(border=True):
    for entry in reversed(st.session_state.logs):
        if "🎉" in entry or "✅" in entry or "Milestone" in entry:
            st.success(entry)
        elif "❌" in entry:
            st.error(entry)
        elif "⚠️" in entry:
            st.warning(entry)
        else:
            st.code(entry, language="text")
