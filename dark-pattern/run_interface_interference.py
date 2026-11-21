# # run_interface_interference.py

# import json
# import sys
# from pathlib import Path

# from common import parse_log
# from interface_interference_type import classify_interface_interference_type
# from interface_interference_subtype import classify_interface_interference_subtype


# def run(paths):
#     results = []

#     for p in paths:
#         pth = Path(p)
#         text = pth.read_text(encoding="utf-8", errors="ignore")
#         turns = parse_log(text)

#         step2 = classify_interface_interference_type(turns)
#         step3 = classify_interface_interference_subtype(turns, step2)

#         results.append({
#             "log_file": pth.name,
#             "num_turns": len(turns),
#             **step2,
#             "step3_subtype_prediction": step3
#         })

#     return results


# def pretty_print(results):
#     print(json.dumps(results, ensure_ascii=False, indent=2))

#     for r in results:
#         top2 = r["step2_type_predictions"][0]
#         top3 = r["step3_subtype_prediction"]

#         print("\n" + "=" * 80)
#         print("FILE:", r["log_file"])
#         print("LAYER1:", r["layer1_assumed"])
#         print("FLAGS:", r.get("flags", []))
#         print("STEP2 TYPE:", top2["type"], "conf=", top2["confidence"], "method=", top2.get("method"))
#         print("STEP3 SUBTYPE:", top3["subtype"], "conf=", top3["confidence"], "method=", top3.get("method"))
#         print("STEP2 REASON:", top2["reason"])
#         print("STEP3 REASON:", top3["reason"])

#         if top2.get("evidence_span"):
#             s, e = top2["evidence_span"]
#             print(f"EVIDENCE SPAN idx={s}..{e}")
#             for t in top2.get("evidence_turns", []):
#                 print(f'[{t["idx"]:02d}] {t["role"]}: {t["text"]}')


# if __name__ == "__main__":
#     if len(sys.argv) <= 1:
#         files = [
#             "The_60s_Channel0.txt",
#             "My_Barber1.txt",
#             "PUBG_MOBILE0.txt"
#         ]
#     else:
#         files = sys.argv[1:]

#     results = run(files)
#     pretty_print(results)

# run_interface_interference.py

import json
import sys
from pathlib import Path

from common import parse_log
from interface_interference_type import classify_interface_interference_type
from interface_interference_subtype import classify_interface_interference_subtype


def run(paths):
    results = []

    for p in paths:
        pth = Path(p)

        if not pth.exists() or not pth.is_file():
            continue

        text = pth.read_text(encoding="utf-8", errors="ignore")
        turns = parse_log(text)

        step2 = classify_interface_interference_type(turns)
        step3 = classify_interface_interference_subtype(turns, step2)

        results.append({
            "log_file": pth.name,
            "num_turns": len(turns),
            **step2,
            "step3_subtype_prediction": step3
        })

    return results


def _print_evidence_block(pred):
    evidence_turn_ids = pred.get("evidence_turn_ids", [])
    evidence_span = pred.get("evidence_span")
    evidence_turns = pred.get("evidence_turns", [])

    if evidence_turn_ids:
        print("EVIDENCE TURN IDS:", evidence_turn_ids)

    if evidence_span:
        s, e = evidence_span
        print(f"EVIDENCE SPAN idx={s}..{e}")

    if evidence_turns:
        print("EVIDENCE TURNS:")
        for t in evidence_turns:
            print(f'[{t["idx"]:02d}] {t["role"]}: {t["text"]}')


def pretty_print(results):
    print(json.dumps(results, ensure_ascii=False, indent=2))

    for r in results:
        primary = r.get("primary_type_prediction", {})
        secondary = r.get("secondary_type_predictions", [])
        ranked = r.get("step2_type_predictions", [])
        top3 = r.get("step3_subtype_prediction", {})

        print("\n" + "=" * 80)
        print("FILE:", r["log_file"])
        print("LAYER1:", r.get("layer1_assumed"))
        print("NUM TURNS:", r.get("num_turns"))
        print("FLAGS:", r.get("flags", []))

        print("\n[PRIMARY TYPE]")
        print(
            "TYPE:",
            primary.get("type"),
            "conf=",
            primary.get("confidence"),
            "method=",
            primary.get("method")
        )
        print("REASON:", primary.get("reason"))

        if secondary:
            print("\n[SECONDARY TYPES]")
            for i, s in enumerate(secondary, start=1):
                print(
                    f"{i}.",
                    s.get("type"),
                    "conf=",
                    s.get("confidence"),
                    "method=",
                    s.get("method")
                )
                print("   reason:", s.get("reason"))
        else:
            print("\n[SECONDARY TYPES]")
            print("None")

        if ranked:
            print("\n[RANKED TYPE CANDIDATES]")
            for i, p in enumerate(ranked, start=1):
                print(
                    f"{i}.",
                    p.get("type"),
                    "conf=",
                    p.get("confidence"),
                    "method=",
                    p.get("method")
                )

        print("\n[STEP3 SUBTYPE]")
        print(
            "SUBTYPE:",
            top3.get("subtype"),
            "conf=",
            top3.get("confidence"),
            "method=",
            top3.get("method")
        )
        print("REASON:", top3.get("reason"))

        print("\n[PRIMARY EVIDENCE]")
        _print_evidence_block(primary)

        if secondary:
            print("\n[SECONDARY EVIDENCE]")
            for i, s in enumerate(secondary, start=1):
                print(f"-- Secondary #{i}: {s.get('type')} --")
                _print_evidence_block(s)


if __name__ == "__main__":
    if len(sys.argv) <= 1:
        files = [
            "The_60s_Channel0.txt",
            "My_Barber1.txt",
            "PUBG_MOBILE0.txt"
        ]
    else:
        files = sys.argv[1:]

    results = run(files)
    pretty_print(results)