"""ZMK Studio から読んだキーマップ（JSON）を、出品者ファームの設定を足して roBa.keymap に書き出す。

使い方: python3 tools/gen_keymap.py tools/studio_snapshot_2026-11-15.json > config/roBa.keymap
"""
import json, sys

km = json.load(open(sys.argv[1]))
beh = {int(k): v for k, v in km["behaviors"].items()}
layers = [[list(b) for b in l["bindings"]] for l in km["layers"]]

# --- Studio で読んだ状態からの変更 ---
TRANS = [beh_id for beh_id, n in beh.items() if n == "Transparent"][0]
MKP = [beh_id for beh_id, n in beh.items() if n == "Mouse Key Press"][0]
KP = [beh_id for beh_id, n in beh.items() if n == "Key Press"][0]
layers[2][13] = [TRANS, 0, 0]          # 仮の「Enter 長押し＋F → L3」をやめ、BS＋Enter の同時長押しにする
layers[4][13] = [MKP, 1, 0]            # トラックボール中: F＝左クリック
layers[4][12] = [MKP, 2, 0]            # トラックボール中: D＝右クリック
layers[0][10] = ["mt_key", 0x700E0, 0x70004]   # A / 長押し Ctrl（打鍵中は長押しにしない）
layers[0][22] = ["mt_key", 0x700E1, 0x7001D]   # Z / 長押し Shift（同上）

def h(v):
    return hex(v)

def binding(b):
    bid, p1, p2 = b
    if bid == "mt_key":
        return f"&mt_key {h(p1)} {h(p2)}"
    n = beh[bid]
    return {
        "Key Press": lambda: f"&kp {h(p1)}",
        "Mod-Tap": lambda: f"&mt {h(p1)} {h(p2)}",
        "Mod-Tap (文字キー)": lambda: f"&mt_key {h(p1)} {h(p2)}",
        "Layer-Tap": lambda: f"&lt {p1} {h(p2)}",
        "LAYER_TAP_TO_0": lambda: f"&lt_to_layer_0 {p1} {h(p2)}",
        "Momentary Layer": lambda: f"&mo {p1}",
        "To Layer": lambda: f"&to {p1}",
        "Toggle Layer": lambda: f"&tog {p1}",
        "Mouse Key Press": lambda: f"&mkp {p1}",
        "Transparent": lambda: "&trans",
        "None": lambda: "&none",
        "Bluetooth": lambda: f"&bt {p1} {p2}",
        "Bootloader": lambda: "&bootloader",
    }[n]()

SENSORS = {0: "&enc_msc_down_up", 2: "&enc_key_press 0xc00e9 0xc00ea", 4: "&enc_msc_down_up"}  # トラックボール中もジョグダイヤルはスクロール（出品者は ⌥⌘←/→）

out = []
w = out.append
w('''/*
 * roBa (Low Profile) キーマップ
 * 出品者ファームウェア（~/src/roba-backup/right_seller.uf2）の設定と、
 * 2026-11-15 時点で ZMK Studio から読んだ配置をもとに tools/gen_keymap.py で作る。
 */
#include <behaviors.dtsi>
#include <dt-bindings/zmk/bt.h>
#include <dt-bindings/zmk/keys.h>
#include <dt-bindings/zmk/pointing.h>

/* 長押しの判定（出品者: 180 ms, tap-preferred, quick-tap 150 ms） */
&mt { flavor = "tap-preferred"; tapping-term-ms = <220>; quick-tap-ms = <150>; };
&lt { flavor = "tap-preferred"; tapping-term-ms = <220>; quick-tap-ms = <150>; };

&trackball {
    automouse-layer = <4>;
};

/ {
    behaviors {
        /* A・Z 用: 直前のキーから 150 ms 以内は必ず文字として扱う */
        mt_key: mt_key {
            compatible = "zmk,behavior-hold-tap";
            label = "MT_KEY";
            display-name = "Mod-Tap (文字キー)";
            #binding-cells = <2>;
            bindings = <&kp>, <&kp>;
            flavor = "tap-preferred";
            tapping-term-ms = <220>;
            quick-tap-ms = <150>;
            require-prior-idle-ms = <150>;
        };

        lt_to_layer_0: lt_to_layer_0 {
            compatible = "zmk,behavior-hold-tap";
            label = "LAYER_TAP_TO_0";
            display-name = "LAYER_TAP_TO_0";
            #binding-cells = <2>;
            bindings = <&mo>, <&to_layer_0>;
            flavor = "hold-preferred";
            tapping-term-ms = <180>;
        };

        mouse_command: mouse_command {
            compatible = "zmk,behavior-hold-tap";
            label = "MOUSE_COMMAND";
            display-name = "MOUSE_COMMAND";
            #binding-cells = <2>;
            bindings = <&kp>, <&mkp>;
            flavor = "tap-preferred";
            tapping-term-ms = <180>;
        };

        alt_tab_rotate: alt_tab_rotate {
            compatible = "zmk,behavior-sensor-rotate";
            label = "ALT_TAB_ROTATE";
            #sensor-binding-cells = <0>;
            bindings = <&kp 0x0c070050>, <&kp 0x0c07004f>;
            tap-ms = <20>;
        };

        enc_msc_down_up: enc_msc_down_up {
            compatible = "zmk,behavior-sensor-rotate";
            label = "ENCODER_MSC_DOWN_UP";
            #sensor-binding-cells = <0>;
            bindings = <&msc MOVE_Y(-80)>, <&msc MOVE_Y(80)>;
            tap-ms = <20>;
        };

        enc_key_press: enc_key_press {
            compatible = "zmk,behavior-sensor-rotate-var";
            label = "enc_key_press";
            #sensor-binding-cells = <2>;
            bindings = <&kp>, <&kp>;
            tap-ms = <5>;
        };
    };

    macros {
        to_layer_0: to_layer_0 {
            compatible = "zmk,behavior-macro-one-param";
            label = "TO_LAYER_0";
            display-name = "TO_LAYER_0";
            #binding-cells = <1>;
            bindings = <&to 0 &macro_param_1to1 &kp MACRO_PLACEHOLDER>;
        };
    };

    /* BS（L1）と Enter（L2）を同時に長押しすると Bluetooth のレイヤー 3 */
    conditional_layers {
        compatible = "zmk,conditional-layers";
        bluetooth {
            if-layers = <1 2>;
            then-layer = <3>;
        };
    };

    /* 出品者の同時押し（50 ms 以内） */
    combos {
        compatible = "zmk,combos";
''')
COMBOS = [
    ("esc", (0, 1), "&to_layer_0 ESCAPE"), ("grave", (1, 2), "&kp GRAVE"),
    ("excl", (2, 3), "&kp EXCLAMATION"), ("at", (3, 4), "&kp AT_SIGN"),
    ("lpar", (6, 7), "&kp LEFT_PARENTHESIS"), ("rpar", (7, 8), "&kp RIGHT_PARENTHESIS"),
    ("del", (8, 9), "&kp DELETE"), ("tab", (11, 12), "&kp TAB"),
    ("shift_tab", (12, 13), "&kp LS(TAB)"), ("spotlight", (13, 14), "&kp LG(SPACE)"),
    ("click", (16, 17), "&mkp 1"), ("cmd_enter", (17, 18), "&kp LG(ENTER)"),
    ("enter", (19, 20), "&kp ENTER"),  # 出品者は J+K「[」・K+L「]」。[ ] はレイヤー 1 にもある
    ("enter2", (20, 21), "&kp ENTER"),
]
for name, (a, b), bnd in COMBOS:
    w(f"        {name} {{ timeout-ms = <50>; key-positions = <{a} {b}>; bindings = <{bnd}>; }};\n")
w("    };\n\n    keymap {\n        compatible = \"zmk,keymap\";\n")
for li, l in enumerate(layers):
    w(f"\n        layer_{li} {{\n            display-name = \"L{li}\";\n            bindings = <\n")
    for i in range(0, len(l), 6):
        w("                " + "  ".join(binding(b) for b in l[i:i + 6]) + "\n")
    w("            >;\n")
    if li in SENSORS:
        w(f"            sensor-bindings = <{SENSORS[li]}>;\n")
    w("        };\n")
w("    };\n};\n")
sys.stdout.write("".join(out))
