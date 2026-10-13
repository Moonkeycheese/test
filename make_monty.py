"""Build "Monty Garage Patterns.amxd" from "Instant_Garage_v3.amxd".

The PATTERNS below (Classic Garage first) live in one embedded coll (---monty)
on the 64th-note path, 2 bars each. The reference device's own patterns are gone.

Grid: 32 chars = 2 bars of 16ths ('|' is ignored). 'X' accent, 'x' hit,
'g' ghost; 'L' accent, '>' hit and 'd' ghost are dragged one 64th late.
Every coll value is "name velocity" pairs. Notes are written on the grid; the
Swing box (0 = straight) pushes the offbeat 16ths late when turned up.

With "Random" selected (or after Rnd), each Go press picks one of RANDOM_SLOTS
combos built at build time: a pattern's kick and snares stay together as its
groove, with the hats and the perc (tambourine, rim) taken from other patterns.

usage: python3 make_monty.py [src.amxd] [out.amxd]
"""
import json, random, struct, sys

PATTERNS = [
    ("Classic Garage", {  # Classic 2-step UK garage
        "kick":    "X.........x.....|X.........x.....",
        "snare":   "....X.......X...|....X.......X..g",
        "hat":     "..x.......x.....|..x.......x.....",
        "open":    "......x.......x.|......x.......x.",
        "shaker":  ".g.x.g.g.g.x.g.g|.g.x.g.g.g.x.g.x",
    }),
    ("Swing Steppa", {  # from the reference device's 2nd pattern (swing now comes from the Swing box)
        "kick":    "x......x..x.....|x......x..x.....",
        "snare":   "....x.......x...|....x.......x...",
        "rim":     ".........x......|.........x...x..",
        "open":    "..x...x...x...x.|..x...x...xx..x.",
        "shaker":  "xxx.x.x.x.xxx.x.|x.x.x.x.x.x.x.x.",
    }),
    ("Tamb Bounce", {  # from the reference device's 3rd pattern
        "kick":    "x.....x.x....x..|x.....x.x....x..",
        "snare":   "....x......x....|....x......x....",
        "hat":     "..x.......x.....|..x.......x.....",
        "open":    ".x.......x......|.x.......x......",
        "shaker":  "x.x.x.xxx.x.x.xx|x.x.x.xxx.x.x.xx",
    }),
    ("Speed 4x4", {  # 4x4 speed garage
        "kick":    "X...x...x...x...|X...x...x...x...",
        "clap":    "....X.......X...|....X.......X...",
        "open":    "..x...x...x...x.|..x...x...x...x.",
        "shaker":  ".g.g.g.g.g.g.g.g|.g.g.g.g.g.g.x.x",
    }),
    ("Skippy", {  # Skippy 2-step with a syncopated kick
        "kick":    "X......x..x.....|X.....x...x..g..",
        "snare":   "....X.......X...|....X.......X...",
        "ghost":   "......g........g|...g.....g......",
        "hat":     "..x...x...x...x.|..x...x...x...x.",
        "shaker":  ".g.g.g.g.g.g.g.g|.g.g.g.g.g.g.g.g",
    }),
    ("Late Step", {  # Future garage, late Burial-style kick
        "kick":    "L........>......|L........>...d..",
        "snare":   "....X......X....|....X......X....",
        "rim":     ".......g........|...g...g........",
        "hat":     "..xg..xg..xg..xg|..xg..xg..xg..xg",
        "shaker":  ".g...g...g...g..|.g...g...g...g..",
    }),
    ("Lazy Half", {  # Half-time future garage with a late kick
        "kick":    "L.........>.....|L......>..>.....",
        "snare":   "........X.......|........X.......",
        "ghost":   "...g.......g....|...g.......g...g",
        "hat":     "..x...x...x...x.|..x...x...x...x.",
        "shaker":  ".g.g...g.g.g...g|.g.g...g.g.g...g",
    }),
]
# Grid char -> velocity and play probability (%). 'L' (accent), '>' and 'd' (ghost) are dragged one 64th late.
DRAGGED = "L>d"
VELOCITY = {"X": 120, "x": 100, "L": 120, ">": 100, "g": 55, "d": 55}
# Grid lanes -> the device's internal instrument names (from the reference device's 11 slots; ride,
# hat4 and hat2 are hidden). Defaults follow the standard Ableton Drum Rack pads, so any kit works.
LANES = {"kick": "kick", "snare": "snare1", "ghost": "snare3", "rim": "clap", "clap": "snare2",
         "hat": "hat1", "open": "hat3", "shaker": "tamb"}
# Order of the 11 instrument toggles in the preset "active" message lists.
INSTRUMENTS = ["kick", "clap", "hat1", "ride", "hat3", "hat4", "hat2", "tamb", "snare1", "snare2", "snare3"]
STEPS = 128  # 64ths in 2 bars, same as the reference device's 64th preset
# shortcut: Rnd picks from combos built at build time, not live; move to a js object if 64 isn't enough.
RANDOM_SLOTS = 64
MAX_LANES = 5  # keep every preset simple
GROUPS = [["kick"], ["snare", "ghost", "clap"], ["hat", "open"], ["shaker", "rim"]]


SNARE_FAMILY = ["snare", "ghost", "rim"]  # never two on the same 16th, and never with the kick


def clashes(grid):
    """16th steps where two of snare/ghost/rim, or the kick and one of them, play together."""
    rows = {k: v.replace("|", "") for k, v in grid.items()}
    hit = lambda lane, i: lane in rows and rows[lane][i] != "."
    return [i for i in range(32) if sum(hit(k, i) for k in SNARE_FAMILY) + hit("kick", i) > 1
            and any(hit(k, i) for k in SNARE_FAMILY)]


def four_on_the_floor(grid):
    kick = grid.get("kick", "").replace("|", "")
    return bool(kick) and all(kick[i] != "." for i in range(0, 32, 4))


def random_combos(n=RANDOM_SLOTS, seed=7):
    """Each combo keeps one preset's kick + snare lanes together (its groove) and takes the hats and the
    perc (shaker, rim) from other presets. Nothing is invented; a 4x4 kick only lives in its own preset;
    no combo repeats a preset or another combo, or stacks kick / snare / ghost / rim (see clashes)."""
    pats = [g for _, g in PATTERNS]
    grooves = [g for g in pats if not four_on_the_floor(g)]
    pick = lambda src, group: {i: src[i] for i in group if i in src}
    flat = lambda g: json.dumps({k: v.replace("|", "") for k, v in g.items()}, sort_keys=True)
    seen, out = {flat(g) for g in pats}, []
    for groove in grooves:
        for hats in pats:
            for perc in pats:
                grid = {**pick(groove, GROUPS[0] + GROUPS[1]), **pick(hats, GROUPS[2]), **pick(perc, GROUPS[3])}
                if flat(grid) not in seen and not clashes(grid):
                    seen.add(flat(grid))
                    out.append(("random", grid))
    random.Random(seed).shuffle(out)  # fixed seed: rebuilding gives the same device
    return out[:n]


def to_coll(patterns, steps=STEPS, sub=4):
    """sub = coll keys per 16th: 4 on the 64th path, 1 on the 16th path (no drags possible there)."""
    hits = {}
    for v, (_, grid) in enumerate(patterns):
        for inst, row in grid.items():
            row = row.replace("|", "")
            assert inst in LANES and len(row) == 32, (inst, row)
            for step, c in enumerate(row):
                if c == ".":
                    continue
                assert sub == 4 or c not in DRAGGED, "drags need the 64th path"
                pos = step * sub + (c in DRAGGED)  # swing is added live by the Swing control
                hits.setdefault(v * steps + pos, []).extend([LANES[inst], VELOCITY[c]])
    return {"count": len(hits), "data": [{"key": k, "value": hits[k]} for k in sorted(hits)]}


def active_flags(grid):
    used = {LANES[k] for k in grid}
    return " ".join("1" if i in used else "0" for i in INSTRUMENTS)


# --- amxd container: 24-byte header, then 'ptch' chunk holding 'mx@c' + files + 'dlst' directory
def unpack(d):
    assert d[24:28] == b"ptch"
    p = d[32:32 + struct.unpack("<I", d[28:32])[0]]
    assert p[:4] == b"mx@c"
    k = struct.unpack(">I", p[12:16])[0]
    assert p[k:k + 4] == b"dlst"
    files, j = [], k + 8
    while j < len(p):
        ln = struct.unpack(">I", p[j + 4:j + 8])[0]
        sub, m, ent = p[j + 8:j + ln], 0, {}
        while m < len(sub):
            sl = struct.unpack(">I", sub[m + 4:m + 8])[0]
            ent[sub[m:m + 4].decode()] = sub[m + 8:m + sl]
            m += sl
        of, sz = struct.unpack(">I", ent["of32"])[0], struct.unpack(">I", ent["sz32"])[0]
        ent["fnam"] = ent["fnam"].rstrip(b"\0")
        ent["data"] = p[of:of + sz]
        files.append(ent)
        j += ln
    return d[:24], p[4:12], files


def pack(head, mxc, files):
    sub = lambda tag, b: tag + struct.pack(">I", len(b) + 8) + b
    body, dl, of = b"", b"", 16
    for f in files:
        name = f["fnam"] + b"\0" * (4 - len(f["fnam"]) % 4)
        dl += sub(b"dire", b"".join([
            sub(b"type", f["type"]), sub(b"fnam", name),
            sub(b"sz32", struct.pack(">I", len(f["data"]))), sub(b"of32", struct.pack(">I", of)),
            sub(b"vers", f["vers"]), sub(b"flag", f["flag"]), sub(b"mdat", f["mdat"])]))
        body += f["data"]
        of += len(f["data"])
    p = b"mx@c" + mxc + struct.pack(">I", of) + body + sub(b"dlst", dl)
    return head + b"ptch" + struct.pack("<I", len(p)) + p


def check_lines(patcher):
    boxes = {b["box"]["id"]: b["box"] for b in patcher["boxes"]}
    for l in patcher["lines"]:
        (s, so), (d, di) = l["patchline"]["source"], l["patchline"]["destination"]
        assert so < boxes[s]["numoutlets"] and di < boxes[d]["numinlets"], l
    for b in boxes.values():
        if "patcher" in b:
            check_lines(b["patcher"])


def check_triggers(patcher):
    for b in patcher["boxes"]:
        t = b["box"].get("text", "").split()
        if t and t[0] in ("t", "trigger"):
            assert all(a in ("b", "f", "i", "l", "s", "clear") for a in t[1:]), b["box"]["text"]
        if "patcher" in b["box"]:
            check_triggers(b["box"]["patcher"])


def check_layout(patcher):
    shown = [b["box"] for b in patcher["boxes"] if b["box"].get("presentation")]
    for i, a in enumerate(shown):
        ax, ay, aw, ah = a["presentation_rect"]
        assert ax + aw <= 150, ("cropped by Live's Generate panel", a["id"])
        for b in shown[i + 1:]:
            bx, by, bw, bh = b["presentation_rect"]
            assert not (ax < bx + bw and bx < ax + aw and ay < by + bh and by < ay + ah), (a["id"], b["id"])


def build(src):
    head, mxc, files = unpack(src)
    assert pack(head, mxc, files) == src, "container round-trip failed"
    patch = json.loads(files[0]["data"].rstrip(b"\0"))
    P = patch["patcher"]
    B = {b["box"]["id"]: b["box"] for b in P["boxes"]}

    def obj(id_, text, rect, ins, outs, outtype="", **kw):
        P["boxes"].append({"box": dict(id=id_, maxclass="newobj", text=text, patching_rect=rect,
                                       numinlets=ins, numoutlets=outs, outlettype=[outtype] * outs, **kw)})

    def msg(id_, text, rect):
        P["boxes"].append({"box": {"id": id_, "maxclass": "message", "numinlets": 2, "numoutlets": 1,
                                   "outlettype": [""], "patching_rect": rect, "text": text}})

    def wire(s, so, d, di, order=None):
        pl = {"source": [s, so], "destination": [d, di]}
        if order is not None:
            pl["order"] = order
        P["lines"].append({"patchline": pl})

    def unwire(src=None, dst=None):
        P["lines"] = [l for l in P["lines"] if not (
            (src is None or l["patchline"]["source"] == src) and (dst is None or l["patchline"]["destination"] == dst))]

    # Pattern switches get a 4th input: the ---monty coll (notes) and the 64th start time.
    for g in ("obj-41", "obj-47"):
        B[g]["inputs"], B[g]["numinlets"] = 4, 5
    # Preset index p: switches clamp to 3; coll offset = max(p - 3, 0) * 128.
    obj("obj-303", "minimum 3", [103.0, 400.0, 64.0, 20.0], 2, 1, "int")
    obj("obj-304", "- 3", [180.0, 400.0, 29.0, 20.0], 2, 1, "int")
    obj("obj-305", "maximum 0", [180.0, 425.0, 64.0, 20.0], 2, 1, "int")
    obj("obj-306", "* %d" % STEPS, [180.0, 450.0, 40.0, 20.0], 2, 1, "int")
    obj("obj-301", "+ 0", [247.0, 360.0, 29.0, 20.0], 2, 1, "int")
    combos = random_combos()
    obj("obj-302", "coll ---monty @embed 1", [247.0, 390.0, 130.0, 20.0], 1, 4,
        coll_data=to_coll(PATTERNS + combos), saved_object_attributes={"embed": 1, "precision": 6})
    P["boxes"].append({"box": {"id": "obj-307", "maxclass": "comment", "numinlets": 1, "numoutlets": 0,
                               "patching_rect": [176.0, 795.0, 420.0, 18.0],
                               "text": "---monty key = (preset - 3) * 128 + 64th step, value = name velocity pairs. Edit patterns in make_monty.py"}})
    # Random: preset >= first_rnd opens a gate so every Go press first picks a new random slot.
    # Rnd button = select "Random" and press Go.
    first_rnd = 3 + len(PATTERNS)  # internal preset numbers: menu index + 3
    obj("obj-330", "t b b", [16.0, 125.0, 34.0, 20.0], 1, 2, "bang")
    obj("obj-331", "gate 1", [60.0, 150.0, 40.0, 20.0], 2, 1)
    obj("obj-332", ">= %d" % first_rnd, [180.0, 475.0, 40.0, 20.0], 2, 1, "int")
    obj("obj-311", "random %d" % len(combos), [60.0, 175.0, 64.0, 20.0], 2, 1, "int")
    obj("obj-312", "+ %d" % first_rnd, [60.0, 200.0, 32.0, 20.0], 2, 1, "int")
    obj("obj-314", "t b b", [470.0, 34.0, 34.0, 20.0], 1, 2, "bang")
    msg("obj-315", "set %d" % len(PATTERNS), [520.0, 34.0, 40.0, 20.0])  # menu index of "Random"
    msg("obj-316", str(first_rnd), [470.0, 60.0, 40.0, 20.0])
    rnd = json.loads(json.dumps(B["obj-88"]))
    rnd.update(id="obj-313", text="Rnd", varname="Rnd", patching_rect=[470.0, 8.0, 40.0, 20.0])
    # Menu, Rnd and Go share the bottom row; Live's Generate panel crops anything past x=150.
    rnd["presentation_rect"] = [98.0, 90.0, 24.0, 16.0]
    B["obj-88"]["presentation_rect"] = [124.0, 90.0, 25.0, 16.0]
    rnd["saved_attribute_attributes"]["valueof"].update(parameter_longname="Rnd", parameter_shortname="Rnd")
    P["boxes"].append({"box": rnd})
    P["parameters"]["obj-313"] = ["Rnd", "Rnd", 0]
    # Go now goes through the re-roll; toggle edits (qlim) skip Go so they keep the current groove.
    unwire(src=["obj-88", 0])
    unwire(src=["obj-40", 0])
    wire("obj-40", 0, "obj-2", 0)
    wire("obj-88", 0, "obj-330", 0)
    wire("obj-330", 1, "obj-331", 1)
    wire("obj-330", 0, "obj-2", 0)
    wire("obj-332", 0, "obj-331", 0)
    wire("obj-331", 0, "obj-311", 0)
    wire("obj-311", 0, "obj-312", 0)
    wire("obj-312", 0, "obj-63", 0)
    wire("obj-313", 0, "obj-314", 0)
    wire("obj-314", 1, "obj-315", 0)
    wire("obj-314", 0, "obj-316", 0)
    wire("obj-315", 0, "obj-14", 0)
    wire("obj-316", 0, "obj-49", 0)
    unwire(src=["obj-20", 0])
    wire("obj-20", 0, "obj-303", 0, 1)
    wire("obj-20", 0, "obj-304", 0, 0)
    wire("obj-20", 0, "obj-332", 0, 2)
    wire("obj-303", 0, "obj-41", 0, 0)
    wire("obj-303", 0, "obj-47", 0, 1)
    wire("obj-304", 0, "obj-305", 0)
    wire("obj-305", 0, "obj-306", 0)
    wire("obj-306", 0, "obj-301", 1)
    wire("obj-68", 0, "obj-301", 0)
    wire("obj-301", 0, "obj-302", 0)
    wire("obj-302", 0, "obj-47", 4)
    wire("obj-56", 0, "obj-41", 4)

    # The reference device's three colls are no longer used: every preset lives in ---monty.
    for c in ("obj-3", "obj-42", "obj-45"):
        B[c]["coll_data"] = {"count": 0, "data": []}
    # Menu index m -> internal preset m + 3, so the switches pick ---monty and its offset is m * 128.
    obj("obj-317", "+ 3", [16.0, 40.0, 29.0, 20.0], 2, 1, "int")
    unwire(src=["obj-14", 0])
    wire("obj-14", 0, "obj-317", 0)
    wire("obj-317", 0, "obj-49", 0)

    # Swing box (under the lanes): 0 = straight, notes on the grid. Turning it up pushes
    # odd 16ths late by swing * 0.00125 beats: 50 = one 64th (MPC 62.5%), 100 = an 8th-triplet-plus (MPC 75%).
    P["boxes"].append({"box": {
        "id": "obj-350", "maxclass": "live.numbox", "numinlets": 1, "numoutlets": 2, "outlettype": ["", "float"],
        "parameter_enable": 1, "patching_rect": [600.0, 600.0, 60.0, 15.0], "fontsize": 9.0,
        "presentation": 1, "presentation_rect": [0.0, 71.0, 72.0, 15.0], "varname": "Swing",
        "saved_attribute_attributes": {"valueof": {
            "parameter_longname": "Swing", "parameter_shortname": "Swing", "parameter_type": 1,
            "parameter_mmin": 0, "parameter_mmax": 100, "parameter_initial": [0], "parameter_initial_enable": 1,
            "parameter_unitstyle": 9, "parameter_units": "Swing %d",
            "parameter_info": "Swing for the offbeat 16ths: 0 = straight on the grid, 30-60 = garage shuffle"}}}})
    P["parameters"]["obj-350"] = ["Swing", "Swing", 0]
    obj("obj-351", "expr $f1*0.00125", [600.0, 625.0, 120.0, 20.0], 1, 1)
    B["obj-55"].update(text="expr $i1*0.25 + ($i1%2)*$f2", outlettype=[""])
    B["obj-56"].update(text="expr $i1*0.0625 + (($i1/4)%2)*$f2", outlettype=[""])
    # Turning Swing re-runs the tool at once: [t b f] sets the swing first, then bangs live.miditool.in
    # directly, the same way Go does (no Random re-roll).
    obj("obj-352", "t b f", [600.0, 610.0, 40.0, 20.0], 1, 2)
    wire("obj-350", 0, "obj-352", 0)
    wire("obj-352", 1, "obj-351", 0)
    wire("obj-352", 0, "obj-2", 0)
    wire("obj-351", 0, "obj-55", 1)
    wire("obj-351", 0, "obj-56", 1)

    # Per hit: unpack "name vel"; velocity (right outlet) lands in dict.pack before the name fires the pitch.
    B["obj-9"].update(text="zl iter 2", numinlets=2, numoutlets=2, outlettype=["", ""])
    obj("obj-320", "unpack s 0", [140.0, 530.0, 60.0, 20.0], 1, 2)
    unwire(src=["obj-9", 0])
    wire("obj-9", 0, "obj-320", 0)
    wire("obj-320", 0, "obj-32", 0)
    wire("obj-320", 1, "obj-30", 1)

    # Preset selector: named menu instead of the 3-way tab, sharing one row with Rnd and Go.
    names = [n for n, _ in PATTERNS] + ["Random"]
    tab = B["obj-14"]
    tab["maxclass"] = "live.menu"
    for k in ("num_lines_patching", "num_lines_presentation"):
        tab.pop(k)
    tab["patching_rect"][3] = 15.0
    tab["presentation_rect"] = [0.0, 90.0, 96.0, 16.0]
    tab["saved_attribute_attributes"]["valueof"].update(parameter_enum=names, parameter_mmax=len(names) - 1)
    B["obj-28"]["presentation"] = 0
    B["obj-28"].pop("presentation_rect")
    P["boxes"] = [b for b in P["boxes"] if b["box"]["id"] != "obj-11"]  # reference author's folder note

    # Grey out unused instrument toggles for each preset.
    sp = B["obj-25"]["patcher"]
    SB = {b["box"]["id"]: b["box"] for b in sp["boxes"]}
    sel = SB["obj-2"]
    n = first_rnd
    sel.update(text="sel " + " ".join(map(str, range(n))), numinlets=n + 1, numoutlets=n + 1,
               outlettype=["bang"] * n + [""])
    # Random slots fall through sel's reject outlet: enable every toggle.
    sp["boxes"].append({"box": {"id": "obj-299", "maxclass": "message", "numinlets": 2, "numoutlets": 1,
                                "outlettype": [""], "patching_rect": [674.0, 45.0, 115.0, 22.0],
                                "text": " ".join(["1"] * len(INSTRUMENTS))}})
    sp["lines"].append({"patchline": {"source": ["obj-2", n], "destination": ["obj-299", 0]}})
    sp["lines"].append({"patchline": {"source": ["obj-299", 0], "destination": ["obj-24", 0]}})
    for v, (_, grid) in enumerate(PATTERNS):
        mid = "obj-%d" % (300 + v)
        sp["boxes"].append({"box": {"id": mid, "maxclass": "message", "numinlets": 2, "numoutlets": 1,
                                    "outlettype": [""], "patching_rect": [674.0 + 120 * v, 77.0, 115.0, 22.0],
                                    "text": active_flags(grid)}})
        sp["lines"].append({"patchline": {"source": ["obj-2", 3 + v], "destination": [mid, 0]}})
        sp["lines"].append({"patchline": {"source": [mid, 0], "destination": ["obj-24", 0]}})

    # Send the notes back right after generating, in the same apply cycle: [t b l clear] clears the
    # note array, generates, then bangs zl.reg into live.miditool.out (no reliance on miditool.in's
    # outlet order, which could leave an apply cycle unanswered).
    B["obj-62"].update(text="t b l clear", numoutlets=3, outlettype=["bang", "", ""])
    unwire(src=["obj-62", 0])
    unwire(src=["obj-62", 1])
    unwire(src=["obj-2", 0])
    unwire(src=["obj-66", 0])
    P["boxes"] = [x for x in P["boxes"] if x["box"]["id"] != "obj-66"]  # its [t b] is no longer used
    wire("obj-62", 1, "obj-59", 0, 0)
    wire("obj-62", 1, "obj-87", 0, 1)
    wire("obj-62", 2, "obj-82", 0)
    wire("obj-62", 0, "obj-53", 0)

    # 8 lanes, 2 columns x 4 rows: (label, toggle, note box, default note). Ghost plays the snare pad quietly.
    UI = [("Kick", "obj-57", "obj-15", 36), ("Snare", "obj-73", "obj-74", 38), ("Ghost", "obj-4", "obj-5", 38),
          ("Rim", "obj-52", "obj-16", 37), ("Clap", "obj-70", "obj-72", 39), ("Hat", "obj-50", "obj-17", 42),
          ("Open", "obj-46", "obj-19", 46), ("Shaker", "obj-64", "obj-69", 44)]
    for k, (label, tog, num, note) in enumerate(UI):
        col, row = divmod(k, 4)
        y = 2.0 + 17.0 * row
        B[tog].update(text=label, texton=label, presentation_rect=[0.0 + 77.0 * col, y, 39.0, 15.0])
        B[num]["presentation_rect"] = [41.0 + 77.0 * col, y, 31.0, 15.0]
        B[num]["saved_attribute_attributes"]["valueof"]["parameter_initial"] = [float(note)]
    for hidden in ("obj-48", "obj-6", "obj-43", "obj-13", "obj-26", "obj-24"):  # ride, hat4, hat2
        B[hidden]["presentation"] = 0
        B[hidden].pop("presentation_rect", None)
    for e in B["obj-10"]["coll_data"]["data"]:  # stored mapping matches the new defaults until Live loads
        e["value"] = {"snare3": [38.0], "tamb": [44.0], "clap": [37.0], "snare2": [39.0]}.get(e["key"], e["value"])

    assert len(PATTERNS) == len({n for n, _ in PATTERNS})
    for name, grid in PATTERNS:
        rows = {k: v.replace("|", "") for k, v in grid.items()}
        assert not clashes(grid), (name, clashes(grid))
        assert len(grid) <= MAX_LANES, (name, "too many lanes")
        assert not any(rows.get("hat", "." * 32)[i] != "." and rows.get("open", "." * 32)[i] != "." for i in range(32)), name
    check_lines(P)
    check_layout(P)
    check_triggers(P)
    files[0]["data"] = json.dumps(patch, indent="\t").encode() + b"\n\0"
    files[0]["fnam"] = b"Monty Garage Patterns.amxd"
    out = pack(head, mxc, files)
    assert unpack(out)[2][0]["data"] == files[0]["data"]
    return out


if __name__ == "__main__":
    src = sys.argv[1] if len(sys.argv) > 1 else "Instant_Garage_v3.amxd"
    dst = sys.argv[2] if len(sys.argv) > 2 else "Monty Garage Patterns.amxd"
    out = build(open(src, "rb").read())
    open(dst, "wb").write(out)
    print("wrote", dst)
