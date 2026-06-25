import os
import json
import signal
import subprocess
import sys
import time
from pathlib import Path
from tqdm import tqdm

# ── Config ───────────────────────────────────────────────────────────────────
REPO_ROOT  = "/home/mediacore/simlingo"
CARLA_ROOT = os.path.expanduser("~/software/carla0915")

AGENT_FILE  = f"{REPO_ROOT}/team_code/agent_simlingo.py"
CHECKPOINT  = f"{REPO_ROOT}/outputs/2026_06_20_20_24_52_simlingo_base_seed_42_dinov2_l14_safety_v13_finetune_10ep/checkpoints/last.ckpt+bench2drive_test"
ROUTE_PATH  = "/home/mediacore/simlingo/leaderboard/data/bench2drive_split"
OUT_ROOT    = f"{REPO_ROOT}/eval_results/Bench2Drive"
EVALUATOR   = f"{REPO_ROOT}/Bench2Drive/leaderboard/leaderboard/leaderboard_evaluator.py"
EVAL_NAME   = Path(CHECKPOINT.split("+", 1)[0]).parents[1].name + "_waypoint_speed_seed42_eval_bench2drive220_rerun"

SEED    = 42
PORT    = 2000
TM_PORT = 8000
TIMEOUT = 600
MAX_RETRIES = 3
MONITOR_INTERVAL = 1.0
SKIP_COMPLETED = True
ROUTE_IDS_TO_RUN = None
FATAL_PATTERNS = (
    "Signal 11 caught",
    "CommonUnixCrashHandler: Signal=11",
    "Segmentation fault",
    "Watchdog exception",
    "while waiting for the simulator",
    "The simulation took longer than",
    "Engine crash handling finished",
    "Failed to stop the scenario, the statistics might be empty",
)
# ─────────────────────────────────────────────────────────────────────────────


def build_env(save_path):
    env = os.environ.copy()
    env["CARLA_ROOT"] = CARLA_ROOT
    env["SAVE_PATH"] = save_path
    existing = env.get("PYTHONPATH", "")
    extra = [
        REPO_ROOT,
        f"{CARLA_ROOT}/PythonAPI/carla",
        f"{CARLA_ROOT}/PythonAPI/carla/dist/carla-0.9.15-py3.7-linux-x86_64.egg",
        f"{REPO_ROOT}/Bench2Drive/leaderboard",
        f"{REPO_ROOT}/Bench2Drive/scenario_runner",
    ]
    env["PYTHONPATH"] = ":".join(extra + ([existing] if existing else []))
    env["SCENARIO_RUNNER_ROOT"] = f"{REPO_ROOT}/Bench2Drive/scenario_runner"
    return env


def kill_carla():
    """Kill any leftover CarlaUE4 processes to free GPU memory.

    A plain pkill can return before Unreal's crash handler and child process
    have actually exited. Wait for the process list to become clean before the
    next route attempt starts, otherwise two CARLA servers can overlap.
    """
    patterns = ("CarlaUE4", "CarlaUE4-Linux-Shipping")

    def find_pids():
        pids = set()
        for pattern in patterns:
            result = subprocess.run(
                ["pgrep", "-f", pattern],
                capture_output=True,
                text=True,
            )
            for line in result.stdout.splitlines():
                try:
                    pid = int(line.strip())
                except ValueError:
                    continue
                if pid != os.getpid():
                    pids.add(pid)
        return sorted(pids)

    for pid in find_pids():
        try:
            os.kill(pid, signal.SIGTERM)
        except ProcessLookupError:
            pass

    deadline = time.time() + 15
    while time.time() < deadline:
        if not find_pids():
            return
        time.sleep(1)

    for pid in find_pids():
        try:
            os.kill(pid, signal.SIGKILL)
        except ProcessLookupError:
            pass

    deadline = time.time() + 10
    while time.time() < deadline:
        if not find_pids():
            return
        time.sleep(1)


def has_fatal_pattern(text):
    return next((pattern for pattern in FATAL_PATTERNS if pattern in text), None)


def terminate_process(proc):
    if proc.poll() is not None:
        return

    try:
        os.killpg(proc.pid, signal.SIGTERM)
    except ProcessLookupError:
        return
    except OSError:
        proc.terminate()

    try:
        proc.wait(timeout=20)
        return
    except subprocess.TimeoutExpired:
        pass

    try:
        os.killpg(proc.pid, signal.SIGKILL)
    except ProcessLookupError:
        return
    except OSError:
        proc.kill()
    proc.wait()


def read_result_status(result_file):
    if not os.path.exists(result_file):
        return False, "missing result json"

    try:
        with open(result_file, "r", encoding="utf-8") as f:
            data = json.load(f)
    except (OSError, json.JSONDecodeError) as exc:
        return False, f"invalid result json: {exc}"

    checkpoint = data.get("_checkpoint", {})
    progress = checkpoint.get("progress", [])
    records = checkpoint.get("records", [])

    if len(progress) < 2 or progress[0] < progress[1]:
        return False, f"incomplete progress: {progress}"
    if not records:
        return False, "empty records"

    entry_status = str(data.get("entry_status", ""))
    if entry_status.lower() in {"started", "crashed", "invalid"}:
        return False, f"bad entry_status: {entry_status}"

    bad_statuses = []
    for record in records:
        status = str(record.get("status", ""))
        status_l = status.lower()
        if status_l == "started" or "failed" in status_l or "crashed" in status_l:
            bad_statuses.append(status)
    if bad_statuses:
        return False, f"bad record status: {bad_statuses}"

    return True, "result complete"


def monitor_process(proc, log_file, start_pos):
    fatal_pattern = None
    observed_log = ""
    read_pos = start_pos

    try:
        with open(log_file, "r", encoding="utf-8", errors="replace") as log_reader:
            while proc.poll() is None:
                log_reader.seek(read_pos)
                chunk = log_reader.read()
                if chunk:
                    read_pos = log_reader.tell()
                    observed_log += chunk
                    fatal_pattern = has_fatal_pattern(observed_log)
                    if fatal_pattern:
                        terminate_process(proc)
                        kill_carla()
                        break
                time.sleep(MONITOR_INTERVAL)

            log_reader.seek(read_pos)
            chunk = log_reader.read()
            if chunk:
                observed_log += chunk
    except KeyboardInterrupt:
        terminate_process(proc)
        kill_carla()
        raise

    return proc.wait(), fatal_pattern or has_fatal_pattern(observed_log), observed_log


def append_log(log_file, message):
    with open(log_file, "a", encoding="utf-8") as f:
        f.write(message + "\n")
        f.flush()


def run_route_attempt(route_path, result_file, log_file, env, attempt):
    kill_carla()

    cmd = [
        sys.executable, "-u", EVALUATOR,
        f"--routes={route_path}",
        "--repetitions=1",
        "--track=SENSORS",
        f"--checkpoint={result_file}",
        f"--timeout={TIMEOUT}",
        f"--agent={AGENT_FILE}",
        f"--agent-config={CHECKPOINT}",
        f"--traffic-manager-seed={SEED}",
        f"--port={PORT}",
        f"--traffic-manager-port={TM_PORT}",
    ]

    if os.path.exists(result_file):
        os.remove(result_file)

    append_log(log_file, f"\n===== attempt {attempt}/{MAX_RETRIES} started =====")
    log_start = os.path.getsize(log_file)
    with open(log_file, "a", encoding="utf-8") as f:
        proc = subprocess.Popen(
            cmd,
            env=env,
            stdout=f,
            stderr=subprocess.STDOUT,
            cwd=REPO_ROOT,
            start_new_session=True,
        )
        try:
            returncode, fatal_pattern, attempt_log = monitor_process(proc, log_file, log_start)
        except KeyboardInterrupt:
            append_log(log_file, f"===== attempt {attempt}/{MAX_RETRIES} interrupted =====")
            raise

    append_log(log_file, f"===== attempt {attempt}/{MAX_RETRIES} exited: {returncode} =====")
    kill_carla()

    if fatal_pattern:
        return False, returncode, f"fatal pattern: {fatal_pattern}"

    fatal_pattern = has_fatal_pattern(attempt_log)
    if fatal_pattern:
        return False, returncode, f"fatal pattern: {fatal_pattern}"

    result_ok, result_reason = read_result_status(result_file)
    if returncode == 0 and result_ok:
        return True, returncode, result_reason

    if returncode != 0:
        return False, returncode, f"exit {returncode}; {result_reason}"
    return False, returncode, result_reason


def run_route(route_path, result_file, log_file, env, route_id):
    Path(log_file).write_text(
        f"[{route_id}] route={route_path}\nmax_retries={MAX_RETRIES}\n",
        encoding="utf-8",
    )

    last_returncode = None
    last_reason = "not started"
    for attempt in range(1, MAX_RETRIES + 1):
        tqdm.write(f"[{route_id}] attempt {attempt}/{MAX_RETRIES}")
        ok, returncode, reason = run_route_attempt(
            route_path, result_file, log_file, env, attempt
        )
        last_returncode = returncode
        last_reason = reason
        append_log(log_file, f"===== attempt {attempt}/{MAX_RETRIES} result: {reason} =====")

        if ok:
            tqdm.write(f"[{route_id}] done on attempt {attempt}")
            return True, returncode, reason

        tqdm.write(f"[{route_id}] retry needed after attempt {attempt}: {reason}")
        kill_carla()

    return False, last_returncode, last_reason


def main():
    routes = sorted(Path(ROUTE_PATH).glob("*.xml"))
    if ROUTE_IDS_TO_RUN is not None:
        routes = [
            route for route in routes
            if route.stem.split("_")[-1].zfill(3) in ROUTE_IDS_TO_RUN
        ]
    if not routes:
        print(f"No route XML files found in {ROUTE_PATH}")
        sys.exit(1)
    print(f"Found {len(routes)} routes. Starting sequential evaluation (seed={SEED}).\n")

    base_dir = os.path.join(OUT_ROOT, EVAL_NAME, f"seed_{SEED}")
    res_dir  = os.path.join(base_dir, "res")
    log_dir  = os.path.join(base_dir, "log")
    viz_dir  = os.path.join(base_dir, "viz")
    os.makedirs(res_dir, exist_ok=True)
    os.makedirs(log_dir, exist_ok=True)
    os.makedirs(viz_dir, exist_ok=True)

    env = build_env(viz_dir)
    succeeded, failed = [], []

    try:
        for route in tqdm(routes, desc="Routes", unit="route"):
            route_id = route.stem.split("_")[-1].zfill(3)
            result_file = os.path.join(res_dir, f"{route_id}_res.json")
            log_file    = os.path.join(log_dir, f"{route_id}.log")

            if SKIP_COMPLETED:
                result_ok, result_reason = read_result_status(result_file)
                if result_ok:
                    succeeded.append(route_id)
                    tqdm.write(f"[{route_id}] skip completed ({result_reason})")
                    continue

            tqdm.write(f"[{route_id}] {route.name}")
            ok, returncode, reason = run_route(route, result_file, log_file, env, route_id)

            if ok:
                succeeded.append(route_id)
            else:
                failed.append(route_id)
                tqdm.write(f"[{route_id}] FAILED after {MAX_RETRIES} attempts ({reason}, exit {returncode}) — log: {log_file}")
    finally:
        kill_carla()

    print(f"\n{'='*55}")
    print(f"Completed: {len(succeeded)}/{len(routes)} routes succeeded")
    if failed:
        print(f"Failed ({len(failed)}): {failed}")
    print(f"Results in: {res_dir}")


if __name__ == "__main__":
    main()
