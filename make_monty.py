"""Build "Monty Garage Patterns.amxd" from "Instant_Garage_v3.amxd".

Keeps the 3 original presets and adds the PATTERNS below. New patterns live in
one embedded coll (---monty) on the device's swung 64th-note path, 2 bars each.

Grid: 32 chars = 2 bars of 16ths ('|' is ignored). 'X' accent, 'x' hit,
'g' ghost; '>' hit and 'd' ghost are dragged one 64th late (see VELOCITY).
Odd 16ths get one 64th of swing (~62%), like the original preset 2.

"Random" / the Rnd button picks one of RANDOM_SLOTS combos pre-rolled at build
time: kick, snare, hat and perc lanes each taken from a random pattern, plus a
couple of hat/perc mutations.

usage: python3 make_monty.py [src.amxd] [out.amxd]
"""
import json, random, struct, sys

PATTERNS = [
    ("2-Step", {
        "kick":   "X.........x.....|X.........x..g..",
        "snare1": "....X.......X...|....X.......X...",
        "hat3":   "..x...x...x...x.|..x...x...x...x.",
        "tamb":   ".g.x.g.x.g.x.g.x|.g.x.g.x.g.x.g.x",
        "clap":   "...........g....|.......g......x.",
    }),
    ("Speed 4x4", {
        "kick":   "X...x...x...x...|X...x...x...x...",
        "snare2": "....X.......X...|....X.......X...",
        "hat3":   "..x...x...x...x.|..x...x...x...x.",
        "hat2":   "...g...g...g...g|...g...g...g...g",
        "tamb":   ".g...g...g...g..|.g...g...g...x.x",
    }),
    ("Skippy", {
        "kick":   "X......x..x.....|X.....x...x..g..",
        "snare1": "....X.......X...|....X.......X...",
        "snare3": "...............g|.........g......",
        "hat1":   "..x...x...x...x.|..x...x...x...x.",
        "hat2":   ".g.g.g.g.g.g.g.g|.g.g.g.g.g.g.g.g",
    }),
    ("Rim Ride", {
        "kick":   "X.........x.....|X..g......x.....",
        "snare1": "....X.......X...|....X.......X...",
        "clap":   "...x..g....x..g.|...x..g....x...x",
        "ride":   "x.g.x.g.x.g.x.g.|x.g.x.g.x.g.x.g.",
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
        "snare3": "......g......g..|..........g....g",
        "clap":   ".......x......g.|...g.......x....",
        "hat2":   ".g.x..g.x.g..x.g|.g.x..g.x.g..x.g",
        "tamb":   "g...x...g...x...|g...x...g...x...",
    }),
    ("Future Half", {
        "kick":   "X.........x.....|X.....x......g..",
        "snare1": "........>.......|........>.......",
        "snare2": "........x.......|........x.......",
        "snare3": "...........d....|...d.......d....",
        "hat3":   "......x.......x.|......x.......x.",
        "tamb":   ".g.g.x.g.g.g.x.g|.g.g.x.g.g.g.x.g",
    }),
    ("Future Roll", {
        "kick":   "X.........x.....|X.......x.x.....",
        "snare1": "....X.......X...|....X.......X...",
        "snare3": ".......d.......d|...........d...d",
        "clap":   "..g.....x.g...x.|..g.....x.g..x..",
        "hat1":   "x.g.x.g.x.g.x.g.|x.g.x.g.x.g.x.g.",
    }),
]
# Grid char -> velocity. '>' and 'd' are also dragged one 64th late.
VELOCITY = {"X": 120, "x": 100, ">": 100, "g": 55, "d": 55}
HUMANIZE = 6  # +/- random velocity per hit, fixed at build time
ORIGINAL_NAMES = ["Orig 1", "Orig 2 Swing", "Orig 3"]
# Order of the 11 instrument toggles in the preset "active" message lists.
INSTRUMENTS = ["kick", "clap", "hat1", "ride", "hat3", "hat4", "hat2", "tamb", "snare1", "snare2", "snare3"]
STEPS = 128  # 64ths in 2 bars, same as the original 64th preset
# shortcut: Rnd picks from combos rolled at build time, not live; move to a js object if 64 isn't enough.
RANDOM_SLOTS = 64
GROUPS = [["kick"], ["snare1", "snare2", "snare3"], ["hat1", "hat2", "hat3"], ["tamb", "clap", "ride"]]


def random_combos(n, seed=7):
    rng = random.Random(seed)  # fixed seed: rebuilding gives the same device
    combos = []
    for _ in range(n):
        grid = {}
        for group in GROUPS:
            src = rng.choice([g for _, g in PATTERNS if any(i in g for i in group)])
            grid.update({i: src[i].replace("|", "") for i in group if i in src})
        for _ in range(2):
            inst = rng.choice([i for i in grid if i in GROUPS[2] + GROUPS[3]])
            row, s = list(grid[inst]), rng.randrange(1, 32)
            if row[s] in ".xg":
                row[s] = "g" if row[s] == "." else "."
            grid[inst] = "".join(row)
        combos.append(("random", grid))
    return combos


def to_coll(patterns):
    rng, hits = random.Random(1), {}
    for v, (_, grid) in enumerate(patterns):
        for inst, row in grid.items():
            row = row.replace("|", "")
            assert inst in INSTRUMENTS and len(row) == 32, (inst, row)
            for step, c in enumerate(row):
                if c == ".":
                    continue
                vel = min(127, VELOCITY[c] + rng.randint(-HUMANIZE, HUMANIZE))
                pos = step * 4 + step % 2 + (c in ">d")
                hits.setdefault(v * STEPS + pos, []).extend([inst, vel])
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


def build(src):
    head, mxc, files = unpack(src)
    assert pack(head, mxc, files) == src, "container round-trip failed"
    patch = json.loads(files[0]["data"].rstrip(b"\0"))
    P = patch["patcher"]
    B = {b["box"]["id"]: b["box"] for b in P["boxes"]}

    def obj(id_, text, rect, ins, outs, outtype="", **kw):
        P["boxes"].append({"box": dict(id=id_, maxclass="newobj", text=text, patching_rect=rect,
                                       numinlets=ins, numoutlets=outs, outlettype=[outtype] * outs, **kw)})

    def wire(s, so, d, di, order=None):
        pl = {"source": [s, so], "destination": [d, di]}
        if order is not None:
            pl["order"] = order
        P["lines"].append({"patchline": pl})

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
    # "Random" menu item / Rnd button: preset = first random slot + random offset.
    first_rnd = len(ORIGINAL_NAMES) + len(PATTERNS)
    obj("obj-310", "sel %d" % first_rnd, [130.0, 23.0, 40.0, 20.0], 2, 2, "bang")
    obj("obj-311", "random %d" % RANDOM_SLOTS, [175.0, 23.0, 64.0, 20.0], 2, 1, "int")
    obj("obj-312", "+ %d" % first_rnd, [245.0, 23.0, 32.0, 20.0], 2, 1, "int")
    obj("obj-314", "t b b", [470.0, 34.0, 34.0, 20.0], 1, 2, "bang")
    P["boxes"].append({"box": {"id": "obj-315", "maxclass": "message", "numinlets": 2, "numoutlets": 1,
                               "outlettype": [""], "patching_rect": [520.0, 34.0, 40.0, 20.0],
                               "text": "set %d" % first_rnd}})
    rnd = json.loads(json.dumps(B["obj-88"]))
    rnd.update(id="obj-313", text="Rnd", varname="Rnd", patching_rect=[470.0, 8.0, 40.0, 20.0])
    rnd["presentation_rect"] = [151.0] + rnd["presentation_rect"][1:]
    rnd["saved_attribute_attributes"]["valueof"].update(parameter_longname="Rnd", parameter_shortname="Rnd")
    P["boxes"].append({"box": rnd})
    P["parameters"]["obj-313"] = ["Rnd", "Rnd", 0]
    P["lines"] = [l for l in P["lines"] if l["patchline"]["source"][0] != "obj-14"]
    wire("obj-14", 0, "obj-310", 0)
    wire("obj-310", 0, "obj-311", 0)
    wire("obj-310", 1, "obj-49", 0)
    wire("obj-311", 0, "obj-312", 0)
    wire("obj-312", 0, "obj-49", 0)
    wire("obj-313", 0, "obj-314", 0)
    wire("obj-314", 1, "obj-315", 0)
    wire("obj-314", 0, "obj-311", 0)
    wire("obj-315", 0, "obj-14", 0)
    P["lines"] = [l for l in P["lines"] if l["patchline"]["source"][0] != "obj-20"]
    wire("obj-20", 0, "obj-303", 0, 1)
    wire("obj-20", 0, "obj-304", 0, 0)
    wire("obj-303", 0, "obj-41", 0, 0)
    wire("obj-303", 0, "obj-47", 0, 1)
    wire("obj-304", 0, "obj-305", 0)
    wire("obj-305", 0, "obj-306", 0)
    wire("obj-306", 0, "obj-301", 1)
    wire("obj-68", 0, "obj-301", 0)
    wire("obj-301", 0, "obj-302", 0)
    wire("obj-302", 0, "obj-47", 4)
    wire("obj-56", 0, "obj-41", 4)

    # Preset selector: named menu instead of the 3-way tab.
    names = ORIGINAL_NAMES + [n for n, _ in PATTERNS] + ["Random"]
    tab = B["obj-14"]
    tab["maxclass"] = "live.menu"
    for k in ("num_lines_patching", "num_lines_presentation"):
        tab.pop(k)
    tab["patching_rect"][3] = tab["presentation_rect"][3] = 15.0
    tab["saved_attribute_attributes"]["valueof"].update(parameter_enum=names, parameter_mmax=len(names) - 1)

    # Grey out unused instrument toggles for each new preset.
    sp = B["obj-25"]["patcher"]
    sel = next(b["box"] for b in sp["boxes"] if b["box"]["id"] == "obj-2")
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

    # Per-hit velocity: coll values become "name vel name vel ..."; originals keep 100.
    for c in ("obj-3", "obj-42", "obj-45"):
        for e in B[c]["coll_data"]["data"]:
            if e["value"] != [0]:
                e["value"] = [x for name in e["value"] for x in (name, 100)]
    B["obj-9"].update(text="zl iter 2", numinlets=2, numoutlets=2, outlettype=["", ""])
    obj("obj-320", "unpack s 0", [140.0, 530.0, 60.0, 20.0], 1, 2)
    P["lines"] = [l for l in P["lines"] if l["patchline"]["source"][0] != "obj-9"]
    wire("obj-9", 0, "obj-320", 0)
    wire("obj-320", 0, "obj-32", 0)
    wire("obj-320", 1, "obj-30", 1)  # dict.pack velocity (cold), set before the pitch fires

    check_lines(P)
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
