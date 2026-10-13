"""Build "Monty Garage Patterns.amxd" from "Instant_Garage_v3.amxd".

Preset 1 is CLASSIC (2 bars of 16ths, in the reference device's first coll).
Presets 2-3 are the reference device's other two patterns, renamed. The
PATTERNS below live in one embedded coll (---monty) on the 64th-note path,
2 bars each.

Grid: 32 chars = 2 bars of 16ths ('|' is ignored). 'X' accent, 'x' hit,
'g' ghost; 'L' accent, '>' hit and 'd' ghost are dragged one 64th late.
Every coll value is "name velocity" pairs. Notes are written on the grid; the
Swing box (50 = straight) pushes the offbeat 16ths late when turned up.

With "Random" selected (or after Rnd), each Go press picks one of RANDOM_SLOTS
combos built at build time: a pattern's kick and snares stay together as its
groove, with the hats and the perc (tambourine, rim) taken from other patterns.

usage: python3 make_monty.py [src.amxd] [out.amxd]
"""
import json, random, struct, sys

CLASSIC = ("Classic Garage", {
    "kick":   "X.........x.....|X.........x.....",
    "snare1": "....X.......X...|....X.......X..g",
    "snare2": "....x.......x...|....x.......x...",
    "hat1":   "..x.......x.....|..x.......x.....",
    "hat3":   "......x.......x.|......x.......x.",
    "tamb":   ".g.x.g.g.g.x.g.g|.g.x.g.g.g.x.g.x",
    "clap":   "...........g....|.......g........",
})
PATTERNS = [
    ("2-Step", {
        "kick":   "X.........x.....|X.........x..g..",
        "snare1": "....X.......X..g|....X.....g.X...",
        "hat3":   "..x...x...x...x.|..x...x...x...x.",
        "tamb":   ".g.x.g.x.g.x.g.x|.g.x.g.x.g.x.g.x",
        "clap":   "...g.......g....|.......g......x.",
    }),
    ("Speed 4x4", {
        "kick":   "X...x...x...x...|X...x...x...x...",
        "snare2": "....X.......X...|....X.......X...",
        "hat3":   "..x...x...x...x.|..x...x...x...x.",
        "hat2":   ".g.g...g.g.g...g|...g...g...g.g.g",
        "tamb":   ".g...g...g...g..|.g...g...g...x.x",
    }),
    ("Skippy", {
        "kick":   "X......x..x.....|X.....x...x..g..",
        "snare1": "....X.......X...|....X.......X...",
        "snare3": "......g........g|...g.....g......",
        "hat1":   "..x...x...x...x.|..x...x...x...x.",
        "hat2":   ".g.g.g.g.g.g.g.g|.g.g.g.g.g.g.g.g",
    }),
    ("Rim Ride", {
        "kick":   "X.........x.....|X..g......x.....",
        "snare1": "....X.......X...|....X.......X...",
        "clap":   "...x..g..g.x..g.|...x..g....x.g.x",
        "ride":   "g.x.g.x.g.x.g.x.|g.x.g.x.g.x.g.x.",
        "hat2":   "...g...g...g...g|...g...g...g...g",
    }),
    ("Broken Fill", {
        "kick":   "X.....x...x.....|X.....x..x......",
        "snare1": "....X.......X...|....X.......Xgxx",
        "clap":   "...........g....|.......g...g....",
        "hat3":   "..x...x.......x.|..x...x...x.....",
        "hat1":   ".g.g.g.g.g.g.g.g|.g.g.g.g.g.g.g..",
    }),
    ("Future Shuffle", {
        "kick":   "X........x......|X.......x.g.....",
        "snare1": "....>.......>...|....>.......>...",
        "snare3": "......g......g..|..........g..g.g",
        "clap":   ".......x......g.|...g.......x....",
        "hat2":   ".g.x..g.x.g..x.g|.g.x..g.x.g..x.g",
        "tamb":   "g...x...g...x...|g...x...g...x...",
    }),
    ("Future Half", {
        "kick":   "X.........x.....|X.....x......g..",
        "snare1": "........>.......|........>.......",
        "snare2": "........>.......|........>.......",
        "snare3": "...g.......d....|...d.......d....",
        "hat3":   "......x.......x.|......x.......x.",
        "tamb":   ".g.g.x.g.g.g.x.g|.g.g.x.g.g.g.x.g",
    }),
    ("Future Roll", {
        "kick":   "X.........x.....|X.......x.x.....",
        "snare1": "....X.......X...|....X.......X...",
        "snare3": ".......d.......d|...........d...d",
        "clap":   "..g.....x.g...x.|..g.....x.g..x..",
        "hat1":   "g.xgg.x.g.xgg.x.|g.x.g.xgg.x.g.xg",
    }),
    # Late-kick future garage: 'L' / '>' / 'd' kicks sit one 64th behind the grid, snares stay on it.
    ("Late Step", {
        "kick":   "L........>......|L........>...d..",
        "snare1": "....X......X....|....X......X....",
        "clap":   ".......g........|...g...g........",
        "hat1":   "..xg..xg..xg..xg|..xg..xg..xg..xg",
        "tamb":   ".g...g...g...g..|.g...g...g...g..",
    }),
    ("Late Bounce", {
        "kick":   "L.....>..>....d.|L.....>...>...d.",
        "snare1": "....X......X....|....X......X....",
        "clap":   "...g...g........|...g...g.....g..",
        "hat1":   "..x...x...x...x.|..x...x...x...x.",
        "hat2":   "...g...g...g...g|...g...g...g...g",
    }),
    ("Lazy Half", {
        "kick":   "L.........>.....|L......>..>.....",
        "snare1": "........X.......|........X.......",
        "snare3": "...g.......g....|...g.......g...g",
        "clap":   "......g.......g.|......g.......g.",
        "hat1":   "..x.g.x.g.x.g.x.|..x.g.x.g.x.g.x.",
        "tamb":   ".g.g...g.g.g...g|.g.g...g.g.g...g",
    }),
    ("Ghost Step", {
        "kick":   "L......>..>.....|L.........>..d..",
        "snare1": "....X......X....|....X......X....",
        "snare3": "...g...g.....g..|.g.....g.....g..",
        "clap":   "......g.........|..........g.....",
        "hat1":   "..xg..xg..xg...g|..xg..xg..xg...g",
        "hat3":   "..............x.|..............x.",
    }),
]
# Grid char -> velocity and play probability (%). 'L' (accent), '>' and 'd' (ghost) are dragged one 64th late.
DRAGGED = "L>d"
VELOCITY = {"X": 120, "x": 100, "L": 120, ">": 100, "g": 55, "d": 55}
OTHER_NAMES = ["Swing Steppa", "Tamb Bounce"]  # the reference device's 2nd and 3rd patterns
# Order of the 11 instrument toggles in the preset "active" message lists.
INSTRUMENTS = ["kick", "clap", "hat1", "ride", "hat3", "hat4", "hat2", "tamb", "snare1", "snare2", "snare3"]
STEPS = 128  # 64ths in 2 bars, same as the reference device's 64th preset
# shortcut: Rnd picks from combos built at build time, not live; move to a js object if 64 isn't enough.
RANDOM_SLOTS = 64
NO_RANDOM_GROOVE = {"Speed 4x4"}  # its four-on-the-floor kick hits the snares: only in its own preset
GROUPS = [["kick"], ["snare1", "snare2", "snare3"], ["hat1", "hat2", "hat3", "ride"], ["tamb", "clap"]]


def random_combos(n, seed=7):
    """Each combo keeps one pattern's kick + snares together (its groove) and takes hats and perc from
    other patterns. No extra hits are invented, and no combo repeats a preset or another combo."""
    rng = random.Random(seed)  # fixed seed: rebuilding gives the same device
    pats = [g for _, g in [CLASSIC] + PATTERNS]
    grooves = [g for name, g in [CLASSIC] + PATTERNS if name not in NO_RANDOM_GROOVE]
    flat = lambda g: json.dumps({k: v.replace("|", "") for k, v in g.items()}, sort_keys=True)
    seen, combos = {flat(g) for g in pats}, []
    while len(combos) < n:
        groove = rng.choice(grooves)
        grid = {i: groove[i] for i in GROUPS[0] + GROUPS[1] if i in groove}
        for group in GROUPS[2:]:
            src = rng.choice([g for g in pats if any(i in g for i in group)])
            grid.update({i: src[i] for i in group if i in src})
        if flat(grid) not in seen:
            seen.add(flat(grid))
            combos.append(("random", grid))
    return combos


def to_coll(patterns, steps=STEPS, sub=4):
    """sub = coll keys per 16th: 4 on the 64th path, 1 on the 16th path (no drags possible there)."""
    hits = {}
    for v, (_, grid) in enumerate(patterns):
        for inst, row in grid.items():
            row = row.replace("|", "")
            assert inst in INSTRUMENTS and len(row) == 32, (inst, row)
            for step, c in enumerate(row):
                if c == ".":
                    continue
                assert sub == 4 or c not in DRAGGED, "drags need the 64th path"
                pos = step * sub + (c in DRAGGED)  # swing is added live by the Swing control
                hits.setdefault(v * steps + pos, []).extend([inst, VELOCITY[c]])
    return {"count": len(hits), "data": [{"key": k, "value": hits[k]} for k in sorted(hits)]}


def active_flags(grid):
    return " ".join("1" if i in grid else "0" for i in INSTRUMENTS)


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
    obj("obj-302", "coll ---monty @embed 1", [247.0, 390.0, 130.0, 20.0], 1, 4,
        coll_data=to_coll(PATTERNS + random_combos(RANDOM_SLOTS)), saved_object_attributes={"embed": 1, "precision": 6})
    P["boxes"].append({"box": {"id": "obj-307", "maxclass": "comment", "numinlets": 1, "numoutlets": 0,
                               "patching_rect": [176.0, 795.0, 420.0, 18.0],
                               "text": "---monty key = (preset - 3) * 128 + 64th step, value = name velocity pairs. Edit patterns in make_monty.py"}})
    # Random: preset >= first_rnd opens a gate so every Go press first picks a new random slot.
    # Rnd button = select "Random" and press Go.
    first_rnd = 1 + len(OTHER_NAMES) + len(PATTERNS)
    obj("obj-330", "t b b", [16.0, 125.0, 34.0, 20.0], 1, 2, "bang")
    obj("obj-331", "gate 1", [60.0, 150.0, 40.0, 20.0], 2, 1)
    obj("obj-332", ">= %d" % first_rnd, [180.0, 475.0, 40.0, 20.0], 2, 1, "int")
    obj("obj-311", "random %d" % RANDOM_SLOTS, [60.0, 175.0, 64.0, 20.0], 2, 1, "int")
    obj("obj-312", "+ %d" % first_rnd, [60.0, 200.0, 32.0, 20.0], 2, 1, "int")
    obj("obj-314", "t b b", [470.0, 34.0, 34.0, 20.0], 1, 2, "bang")
    msg("obj-315", "set %d" % first_rnd, [520.0, 34.0, 40.0, 20.0])
    msg("obj-316", str(first_rnd), [470.0, 60.0, 40.0, 20.0])
    rnd = json.loads(json.dumps(B["obj-88"]))
    rnd.update(id="obj-313", text="Rnd", varname="Rnd", patching_rect=[470.0, 8.0, 40.0, 20.0])
    # Menu, Rnd and Go share the bottom row; Live's Generate panel crops anything past x=150.
    rnd["presentation_rect"] = [98.0, 106.0, 24.0, 16.0]
    B["obj-88"]["presentation_rect"] = [124.0, 106.0, 25.0, 16.0]
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

    # Preset 1 becomes CLASSIC: 2 bars of 16ths in the reference device's first coll.
    B["obj-3"]["coll_data"] = to_coll([CLASSIC], steps=32, sub=1)
    B["obj-65"]["text"] = "% 32"
    # Every coll value becomes "name velocity" pairs; the reference patterns play at velocity 100.
    for c in ("obj-42", "obj-45"):
        for e in B[c]["coll_data"]["data"]:
            if e["value"] != [0]:
                e["value"] = [x for name in e["value"] for x in (name, 100)]
    # Its 64th preset had swing baked in (+1 64th on odd 16ths): straighten it, notes stay on the grid.
    # Rests ("0" values) are dropped: a missing key plays nothing, same as a 0.
    data = [e for e in B["obj-42"]["coll_data"]["data"] if e["value"] != [0]]
    keys = {e["key"] for e in data}
    for e in data:
        if e["key"] % 4:
            assert e["key"] % 4 == 1 and (e["key"] // 4) % 2 == 1 and e["key"] - 1 not in keys, e
            e["key"] -= 1
    data.sort(key=lambda e: e["key"])
    assert len({e["key"] for e in data}) == len(data)
    B["obj-42"]["coll_data"] = {"count": len(data), "data": data}

    # Swing box (in the empty grid cell under Snare3): 50 = straight, notes on the grid. Turning it up pushes
    # odd 16ths late by (swing * 0.005 - 0.25) beats (62.5 = one 64th); Live's Auto Apply re-runs the tool.
    P["boxes"].append({"box": {
        "id": "obj-350", "maxclass": "live.numbox", "numinlets": 1, "numoutlets": 2, "outlettype": ["", "float"],
        "parameter_enable": 1, "patching_rect": [600.0, 600.0, 60.0, 15.0], "fontsize": 9.0,
        "presentation": 1, "presentation_rect": [77.0, 86.5, 72.0, 15.0], "varname": "Swing",
        "saved_attribute_attributes": {"valueof": {
            "parameter_longname": "Swing", "parameter_shortname": "Swing", "parameter_type": 1,
            "parameter_mmin": 50, "parameter_mmax": 75, "parameter_initial": [50], "parameter_initial_enable": 1,
            "parameter_unitstyle": 9, "parameter_units": "Swing %d",
            "parameter_info": "Swing for the offbeat 16ths: 50 = straight on the grid, 58-66 = garage shuffle"}}}})
    P["parameters"]["obj-350"] = ["Swing", "Swing", 0]
    obj("obj-351", "expr $f1*0.005 - 0.25", [600.0, 625.0, 120.0, 20.0], 1, 1)
    B["obj-55"].update(text="expr $i1*0.25 + ($i1%2)*$f2", outlettype=[""])
    B["obj-56"].update(text="expr $i1*0.0625 + (($i1/4)%2)*$f2", outlettype=[""])
    wire("obj-350", 0, "obj-351", 0)
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
    names = [CLASSIC[0]] + OTHER_NAMES + [n for n, _ in PATTERNS] + ["Random"]
    assert len(names) == first_rnd + 1
    tab = B["obj-14"]
    tab["maxclass"] = "live.menu"
    for k in ("num_lines_patching", "num_lines_presentation"):
        tab.pop(k)
    tab["patching_rect"][3] = 15.0
    tab["presentation_rect"] = [0.0, 106.0, 96.0, 16.0]
    tab["saved_attribute_attributes"]["valueof"].update(parameter_enum=names, parameter_mmax=len(names) - 1)
    B["obj-28"]["presentation"] = 0
    B["obj-28"].pop("presentation_rect")
    P["boxes"] = [b for b in P["boxes"] if b["box"]["id"] != "obj-11"]  # reference author's folder note

    # Grey out unused instrument toggles for each preset.
    sp = B["obj-25"]["patcher"]
    SB = {b["box"]["id"]: b["box"] for b in sp["boxes"]}
    SB["obj-6"]["text"] = active_flags(CLASSIC[1])
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
    open(dst, "wb").write(build(open(src, "rb").read()))
    print("wrote", dst)
