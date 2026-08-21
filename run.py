#!/usr/bin/env python3
"""
YT Shorts Engine - Unified entry point

Usage:
  python run.py server              Start API server
  python run.py worker              Start background worker
  python run.py ui                  Start review UI
  python run.py setup               First-time setup
  python run.py graph               Curiosity graph status
  python run.py belief <action>     review | approve <id> | reject <id> | auto-apply | list
  python run.py experiment [list|variables]   Suggest / inspect experiments
  python run.py predict <id> [--metric retention]
  python run.py outcome <id> <value> [--metric retention]
  python run.py analyst <note <id>|propose>
  python run.py ingest <csv> [--channel NAME] [--dry-run] [--api] [--force]
  python run.py experiment run <id> [--execute] [--channel NAME]
  python run.py experiment absorb <id> [--metric retention]
  python run.py loop [--execute] [--channel NAME] [--metric retention]
  python run.py gate [--apply]       Calibrated belief review + adopt
  python run.py signals [list] | apply <id>
  python run.py intel <channel|url> [--limit N] [--dry-run]  Competitor RSS intel
  python run.py intel --report       Digest of stored competitor videos
  python run.py intel claims         Patterns -> testable claims
  python run.py intel apply          Land claims as beliefs (deduped)
"""
import sys
import os
import subprocess


def _arg_after(args, flag, default=None):
    """Return the value after `flag` in `args`, or `default` if missing/last."""
    try:
        idx = args.index(flag)
        return args[idx + 1]
    except (ValueError, IndexError):
        return default


if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")


def cmd_server():
    from app.main import start
    start()


def cmd_worker():
    from app.worker.generator import VideoGeneratorWorker
    worker = VideoGeneratorWorker()
    worker.run_forever(poll_interval=30)


def cmd_ui():
    ui_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "app", "ui", "review.py"))
    sys.exit(subprocess.call(["streamlit", "run", ui_path, "--server.port", "8501"]))


def cmd_setup():
    print("""
=== YT Shorts Engine Setup ===

1. Create a .env file from .env.example:
   cp .env.example .env
   Edit .env with your API keys:
   - PEXELS_API_KEY (required) - from https://www.pexels.com/api/
   - REDDIT_CLIENT_ID/SECRET (optional) - from https://www.reddit.com/prefs/apps
   - OPENAI_API_KEY (optional) - from https://platform.openai.com

2. YouTube Upload Setup:
   - Go to https://console.cloud.google.com/
   - Create a project → Enable YouTube Data API v3
   - Create OAuth 2.0 credentials → Download as client_secrets.json
   - Place client_secrets.json in this directory

3. Install dependencies:
   pip install -r requirements.txt

4. Download a font:
   mkdir -p app/assets/fonts
   Download Roboto-Bold.ttf into app/assets/fonts/

5. Run:
   python run.py server    (API on :8000)
   python run.py ui        (Review UI on :8501)
   python run.py worker    (Background video generator)

Or use Docker:
   docker compose up
""")


# =============================================================================
# Curiosity Intelligence CLI
# =============================================================================

def _graph():
    from curiosity.graph import GraphStore
    store = GraphStore()
    s = store.summary()
    print("🧠 CURIOSITY GRAPH STATUS")
    print("=" * 50)
    for ntype, count in sorted(s["nodes"].items()):
        print(f"   {ntype:20s} {count}")
    print(f"   {'edges':20s} {s['edges']}")
    print(f"   {'features':20s} {s['features']}")
    print(f"   {'beliefs':20s} {s['beliefs']}")
    print(f"   {'analytics':20s} {s.get('analytics', 0)} videos with analytics payload")
    store.close()


def _belief(args):
    from curiosity.graph import GraphStore
    from curiosity.beliefs import BeliefStore

    beliefs = BeliefStore()
    if not args:
        print("Usage: python run.py belief <review|approve|reject|auto-apply|list> [id]")
        return

    action = args[0]
    if action == "list":
        for b in beliefs.list_beliefs():
            lo, hi = b.interval()
            print(f"  [{b.id}] {b.status:10s} conf={b.confidence:.2f} N={b.n} "
                  f"({b.n_pos}p/{b.n_neg}n) — {b.claim[:70]}")
            if b.mechanic == "linear":
                print(f"        slope={b.extra.get('slope')} CI=[{lo}, {hi}] r2={b.extra.get('r2')}")
    elif action == "review":
        pending = [b for b in beliefs.list_beliefs() if b.status == "proposed"]
        if not pending:
            print("No beliefs awaiting review.")
        for b in pending:
            print(f"  [{b.id}] {b.claim}")
            print(f"        {b.statement}")
            print(f"        mechanic={b.mechanic} conf={b.confidence:.2f} created={b.created_at}")
    elif action == "approve" and len(args) > 1:
        b = beliefs.approve(int(args[1]))
        print(f"✅ Confirmed belief #{b.id}: {b.claim}")
    elif action == "reject" and len(args) > 1:
        b = beliefs.reject(int(args[1]))
        print(f"❌ Rejected belief #{b.id}: {b.claim}")
    elif action == "auto-apply":
        n = beliefs.auto_apply()
        print(f"🔁 Auto-applied {n} overdue 'proposed' beliefs as 'provisional'.")
    else:
        print("Unknown belief action.")


def _experiment(args):
    from curiosity.graph import GraphStore
    from curiosity.beliefs import BeliefStore
    from curiosity.scheduler import Scheduler
    from curiosity.loop import LearningLoop

    graph, beliefs = GraphStore(), BeliefStore()
    sched = Scheduler(graph, beliefs)
    if args and args[0] == "list":
        for ex in sched.list_experiments():
            print(f"  [{ex['id']}] {ex['status']:10s} var={ex['treatment_var']} "
                  f"belief={ex['belief_id']} — {ex['hypothesis'][:80]}")
        return
    if args and args[0] == "variables":
        for v in sched.actionable_variables():
            print(f"  {v['key']:20s} {v['label']}  (control: {v['control']})")
        return
    if args and args[0] == "run":
        loop = LearningLoop(graph=graph, beliefs=beliefs, scheduler=sched)
        if len(args) < 2:
            print("Usage: python run.py experiment run <id> [--execute] [--channel NAME]")
            return
        exp_id = int(args[1])
        execute = "--execute" in args
        channel = "sigma"
        if "--channel" in args:
            channel = args[args.index("--channel") + 1]
        res = loop.run_experiment(exp_id, execute=execute, channel=channel)
        if not res.get("ok"):
            print(f"⚠️  {res.get('error')}")
            return
        print(f"🚀 Experiment #{exp_id} marked running")
        print(f"   {res['command']}")
        if res.get("spawned"):
            print(f"   exit code: {res.get('exit_code')}")
        return
    if args and args[0] == "absorb":
        loop = LearningLoop(graph=graph, beliefs=beliefs, scheduler=sched)
        if len(args) < 2:
            print("Usage: python run.py experiment absorb <id> [--metric retention]")
            return
        metric = "retention"
        if "--metric" in args:
            metric = args[args.index("--metric") + 1]
        res = loop.absorb_outcomes(int(args[1]), metric=metric)
        if not res.get("ok"):
            print(f"⚠️  {res.get('error')}")
            return
        print(f"🧪 Experiment #{res['experiment_id']} (belief #{res['belief_id']}, "
              f"{res['samples']} outcome(s))")
        for r in res["records"]:
            if r["type"] == "binary":
                print(f"   treatment beat control: {r['success']}  "
                      f"(ctl {r['control_mean']:.3f} vs trt {r['treatment_mean']:.3f})")
            else:
                print(f"   sample x={r['x']:.3f} y={r['y']:.3f}")
        if res.get("completed"):
            print(f"   ✅ experiment #{res['experiment_id']} completed")
        return
    design = sched.suggest_experiment()
    ex_id = sched.save_experiment(design)
    print("🧪 SUGGESTED EXPERIMENT")
    print("=" * 50)
    print(f"  hypothesis : {design.hypothesis}")
    print(f"  treatment  : {design.treatment_var}  levels={design.levels}")
    print(f"  fixed      : {design.fixed_vars}")
    print(f"  saved as   : experiment #{ex_id}")
    print("  run with   : python batch_generate.py --from-design %d" % ex_id)


def _intel(args):
    from curiosity.intel import CompetitorIntel

    if not args:
        print("Usage: python run.py intel <channel_id|channel_url> [--limit N] [--dry-run]")
        print("       python run.py intel --report | claims | apply")
        return

    if args[0] == "--report":
        print(CompetitorIntel().report())
        return

    if args[0] == "claims":
        intel = CompetitorIntel()
        pat = intel.aggregate()
        claims = intel.intel_claims(pat)
        print("🏭 COMPETITOR PATTERNS -> TESTABLE CLAIMS")
        print("=" * 60)
        for k in ("question_hook_ratio", "numbered_ratio", "vs_ratio",
                  "posts_last_7d", "median_views"):
            print(f"  {k:20s} : {pat.get(k, 0.0)}")
        print("-" * 60)
        if not claims:
            print("  No pattern crossed its threshold — nothing to propose.")
            return
        for c in claims:
            print(f"  💡 {c['claim']}  (observed {c['observed']:.2f})")
            print(f"     {c['statement']}")
            print(f"     -> keyword '{c['keyword']}' | {c['mechanic']}")
        print("-" * 60)
        print("  Land these as beliefs with: python run.py intel apply")
        return

    if args[0] == "apply":
        intel = CompetitorIntel()
        res = intel.apply_claims()
        print("🏭 INTEL CLAIMS APPLIED")
        print("=" * 60)
        print(f"  created : {len(res['created'])} new belief(s): {res['created']}")
        print(f"  existing: {len(res['existing'])} matched belief(s): {res['existing']}")
        ev = intel.graph.conn.execute(
            "SELECT COUNT(*) AS n FROM evidence WHERE kind = 'competitor'"
        ).fetchone()
        print(f"  competitor evidence rows: {ev['n']}")
        return

    channel = args[0]
    if "youtube.com" in channel:
        channel = channel.split("/")[-1]
    limit = 50
    if "--limit" in args:
        limit = int(args[args.index("--limit") + 1])
    dry_run = "--dry-run" in args

    intel = CompetitorIntel()
    videos = intel.fetch_feed(channel, limit=limit)
    if not videos:
        print(f"⚠️  No videos fetched: {intel.last_error}")
        return
    print(f"📡 Fetched {len(videos)} competitor videos from channel {channel}")

    report = intel.ingest(videos, dry_run=dry_run)
    print("=" * 50)
    print(f"  added    : {report['added']} competitor videos")
    print(f"  existing : {report['existing']}")
    print(f"  entities : {report['linked_entities']} entity links")
    print(f"  evidence : {report['evidenced']} evidence rows")

    pat = intel.patterns(videos)
    print("-" * 50)
    print(f"  question hooks : {pat['question_hook_ratio']*100:.0f}% of titles")
    print(f"  numbered titles: {pat['numbered_ratio']*100:.0f}%")
    print(f"  posts / 7 days : {pat['posts_last_7d']}")
    if pat["median_views"]:
        print(f"  median views   : {pat['median_views']:,.0f}")


def _gate(args):
    from curiosity.graph import GraphStore
    from curiosity.beliefs import BeliefStore
    from curiosity.scheduler import Scheduler
    from curiosity.gate import Gate

    graph, beliefs = GraphStore(), BeliefStore()
    sched = Scheduler(graph, beliefs)
    gate = Gate(beliefs, scheduler=sched)

    if "--apply" in args:
        created = gate.apply()
        if not created:
            print("✅ Nothing is ready to adopt yet (no belief reached the threshold).")
            return
        for s in created:
            print(f"  ✅ Signal #{s['id']}: {s['signal_type']:14s} {s['target']} "
                  f"-> {s['value']}  (belief #{s['belief_id']})")
        print("  Apply with: python run.py signals apply <id>")
        return

    print("🚦 GATE — belief calibration status")
    print("=" * 60)
    for d in gate.decisions():
        icon = {"adopt": "🟢", "test": "🟡", "drop": "🔴"}.get(d.decision, "⚪")
        print(f"  {icon} [{d.belief_id}] {d.decision:5s} conf={d.confidence:.2f} "
              f"N={d.n:3d}  {d.claim[:60]}")
        print(f"        {d.reason}"
              + (f"  -> {d.target}: {d.value}" if d.value else ""))
    print("-" * 60)
    n_adopt = sum(1 for d in gate.decisions() if d.decision == "adopt")
    print(f"  {n_adopt} belief(s) ready to adopt. Run: python run.py gate --apply")


def _signals(args):
    from curiosity.gate import Gate
    from curiosity.beliefs import BeliefStore

    gate = Gate(BeliefStore())
    if not args or args[0] == "list":
        for s in gate.list_signals():
            print(f"  [{s['id']}] {s['status']:9s} {s['signal_type']:14s} "
                  f"{s['target'] or '-'} -> {s['value']}  (belief #{s['belief_id']})")
        return
    action = args[0]
    if action == "apply" and len(args) > 1:
        s = gate.mark_applied(int(args[1]))
        if s:
            print(f"✅ Signal #{s['id']} applied: {s['signal_type']} "
                  f"{s['target']} -> {s['value']}")
        else:
            print(f"No signal #{args[1]}")
    else:
        print("Usage: python run.py signals [list] | apply <id>")


def _loop(args):
    from curiosity.loop import LearningLoop

    execute = "--execute" in args
    channel = _arg_after(args, "--channel", "sigma")
    metric = _arg_after(args, "--metric", "retention")

    loop = LearningLoop()
    # Resolve batch_generate.py relative to this file so the command is
    # correct regardless of the working directory the loop is invoked from.
    script_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "batch_generate.py")
    loop.script_path = script_path
    report = loop.cycle(execute=execute, channel=channel, metric=metric)

    print("🔄 LEARNING LOOP CYCLE")
    print("=" * 50)
    if report["absorbed"]:
        print(f"  absorbed  : {len(report['absorbed'])} running experiment(s)")
        for rep in report["absorbed"]:
            print(f"      exp #{rep.get('experiment_id')}: {rep.get('samples')} outcome(s), "
                  f"{len(rep.get('records', []))} belief update(s)")
    else:
        print("  absorbed  : 0")
    print(f"  experiment: {report['experiment']}")
    print(f"  command   : {report['command']}")
    if report["spawned"]:
        print("  spawned   : yes")
    if report["note"]:
        print(f"  note      : {report['note']}")


def _predict(args):
    from curiosity.graph import GraphStore
    from curiosity.predict import Predictor

    if not args:
        print("Usage: python run.py predict <video_id> [--metric retention]")
        return
    video_id = int(args[0])
    metric = "retention"
    if "--metric" in args:
        metric = args[args.index("--metric") + 1]

    graph = GraphStore()
    pred = Predictor(graph).predict(graph.get_video_features(video_id), metric=metric)
    print(f"🔮 PREDICTION ({metric}) for video #{video_id}")
    print(f"   estimate  : {pred.estimate:.4f}")
    print(f"   95% CI    : [{pred.ci_lo:.4f}, {pred.ci_hi:.4f}]")
    print(f"   confidence: {pred.confidence:.2f}")
    print(f"   trained N : {pred.n}   r2: {pred.r2}")
    print(f"   features  : {len(pred.used_features)} used")
    if pred.n < 10:
        print("   ⚠️  Low N — treat the interval as a wide prior, not a forecast.")


def _outcome(args):
    from curiosity.graph import GraphStore

    if len(args) < 3:
        print("Usage: python run.py outcome <video_name> <metric> <value>")
        return
    video_name = args[0]
    metric = args[1]
    value = float(args[2])

    graph = GraphStore()
    node = graph.find_node("video", video_name)
    if node is None:
        print(f"❌ No video node found with name '{video_name}'")
        return
    graph.record_outcome(node["id"], metric, value)
    print(f"✅ Recorded {metric}={value} for video '{video_name}' (node #{node['id']})")


def _ingest(args):
    from curiosity.ingest import Ingestor

    if not args:
        print("Usage: python run.py ingest <csv> [--channel NAME] [--dry-run] [--api] [--force]")
        return
    csv_path = args[0]
    channel = _arg_after(args, "--channel", "")
    dry_run, use_api, force = False, False, False
    if "--dry-run" in args:
        dry_run = True
    if "--api" in args:
        use_api = True
    if "--force" in args:
        force = True

    ing = Ingestor()
    if use_api:
        records = ing.from_api(force=force)
        if not records:
            print(f"⚠️  API fetch returned nothing: {ing.last_error}")
            return
        print(f"📡 Fetched {len(records)} videos from YouTube API")
    else:
        records = ing.from_csv(csv_path, channel=channel, force=force)
        if not records:
            print(f"⚠️  No records parsed from CSV: {ing.last_error}")
            return
        print(f"📄 Parsed {len(records)} rows from {csv_path}")

    report = ing.sync(records, dry_run=dry_run)
    print("=" * 50)
    print(f"  matched   : {report['matched']} graph videos")
    print(f"  outcomes  : {report['outcomes']} outcome nodes {'(dry run)' if dry_run else ''}")
    print(f"  analytics : {report['analytics']} payloads updated")
    if report["unmatched"]:
        print(f"  unmatched : {len(report['unmatched'])}  (add a 'local name' column to match)")
        for t in report["unmatched"][:10]:
            print(f"      - {t}")


def _analyst(args):
    from curiosity.graph import GraphStore
    from curiosity.beliefs import BeliefStore
    from curiosity.analyst import Analyst

    graph, beliefs = GraphStore(), BeliefStore()
    analyst = Analyst(graph, beliefs)

    if not args:
        print("Usage: python run.py analyst <note|propose> [belief_id]")
        return
    action = args[0]
    if action == "note" and len(args) > 1:
        b = beliefs.get_belief(int(args[1]))
        if not b:
            print(f"No belief #{args[1]}")
            return
        note = analyst.generate_learning_note(b)
        print("📝 LEARNING NOTE")
        print("=" * 50)
        print(note)
    elif action == "propose":
        ids = analyst.propose_claims()
        print(f"💡 Proposed {len(ids)} new belief(s): {ids}")
        print("   Review with: python run.py belief review")
    else:
        print("Unknown analyst action.")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    command = sys.argv[1]
    commands = {
        "server": cmd_server,
        "worker": cmd_worker,
        "ui": cmd_ui,
        "setup": cmd_setup,
        "graph": lambda: _graph(),
        "belief": lambda: _belief(sys.argv[2:]),
        "experiment": lambda: _experiment(sys.argv[2:]),
        "predict": lambda: _predict(sys.argv[2:]),
        "outcome": lambda: _outcome(sys.argv[2:]),
        "analyst": lambda: _analyst(sys.argv[2:]),
        "ingest": lambda: _ingest(sys.argv[2:]),
        "loop": lambda: _loop(sys.argv[2:]),
        "gate": lambda: _gate(sys.argv[2:]),
        "signals": lambda: _signals(sys.argv[2:]),
        "intel": lambda: _intel(sys.argv[2:]),
    }

    if command in commands:
        commands[command]()
    else:
        print(f"Unknown command: {command}")
        print(__doc__)
