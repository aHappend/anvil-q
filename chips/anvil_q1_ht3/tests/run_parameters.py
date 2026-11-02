"""Public ABI, startup/CSR smoke, and executable illegal-parameter diagnostics."""

import argparse
import hashlib
import json
from pathlib import Path
import re
import sys
import uuid

sys.path.insert(0, str(Path(__file__).resolve().parent))
from execution import ROOT, execute, hashes, relative, remaining, timestamp


SMALL = dict(NUM_LAYERS=1,HIDDEN_SIZE=8,INTERMEDIATE_SIZE=8,NUM_Q_HEADS=1,
             NUM_KV_HEADS=1,HEAD_DIM=8,GROUP_SIZE=1,VOCAB_SIZE=1,MAX_SEQ_LEN=1,
             TILE_BEATS=1,KV_WINDOW=1,FLASH_TILE=3)
NONPOWER = dict(NUM_LAYERS=1,HIDDEN_SIZE=24,INTERMEDIATE_SIZE=40,NUM_Q_HEADS=3,
                NUM_KV_HEADS=1,HEAD_DIM=8,GROUP_SIZE=8,VOCAB_SIZE=17,MAX_SEQ_LEN=17,
                TILE_BEATS=3,KV_WINDOW=3,FLASH_TILE=128)
DEFAULT = dict(NUM_LAYERS=24,HIDDEN_SIZE=896,INTERMEDIATE_SIZE=4864,NUM_Q_HEADS=14,
               NUM_KV_HEADS=2,HEAD_DIM=64,GROUP_SIZE=128,VOCAB_SIZE=151936,
               MAX_SEQ_LEN=32768,TILE_BEATS=256,KV_WINDOW=128,FLASH_TILE=16)


def csr_vectors():
    rows = [(0x0000,0,0,0,0x02000001), (0x0154,0,0,0,0x03000003),
            (0x0100,0,0,0,0), (0x0104,0,0,0,0)]
    for address in (0x0150,0x0158,0x015C,0x0160):
        rows.append((address,0,0,0,0))
    for address in [0x010C,*range(0x0138,0x0150,4),*range(0x0164,0x0180,4)]:
        rows.extend([(address,0,0,0,0),(address,1,1,1,0)])
    rows.extend([(0x0154,1,0,1,0),(0x0108,1,0,1,0),(0x0151,0,0,1,0)])
    for address,valid,invalid in ((0x0150,7,8),(0x0158,0x1000,1),
                                 (0x015C,1,2),(0x0160,64,1)):
        rows.extend([(address,1,valid,0,0),(address,0,0,0,valid),
                     (address,1,invalid,1,0),(address,0,0,0,valid)])
    for mode in (0,1,2):
        rows.extend([(0x0100,1,mode,0,0),(0x0100,0,0,0,mode),
                     (0x000C,0,0,0,int(mode != 2))])
    rows.extend([(0x0100,1,3,1,0),(0x0100,0,0,0,2),
                 (0x0100,1,16,1,0),(0x0100,0,0,0,2)])
    for threshold in (0,0x8000,0x3F80):
        rows.extend([(0x0104,1,threshold,0,0),(0x0104,0,0,0,threshold)])
    for bad in (0xBF80,0x7F80,0x7FC0,0x10000):
        rows.extend([(0x0104,1,bad,1,0),(0x0104,0,0,0,0x3F80)])
    return rows


def check_abi():
    parent = (ROOT/"anvil_q1_ht2_reference/rtl/anvil_q1_ht2_top.sv").read_text()
    product = (ROOT/"rtl/anvil_q1_ht3_top.sv").read_text()
    def ports(text):
        return re.sub(r"\s+", " ", text.split(") (",1)[1].split(");",1)[0]).strip()
    if ports(parent) != ports(product):
        raise AssertionError("top ordered external port declarations differ from supplied HT2")
    return hashlib.sha256(ports(parent).encode()).hexdigest()


def compact_smoke(directory, simulator):
    rows = csr_vectors()
    vectors = directory/"vectors.txt"
    with vectors.open("x") as out:
        for address,write,data,error,expected in rows:
            out.write(f"{address:04x} {write} {data:08x} {error} {expected:08x}\n")
    sources = [relative(p) for p in sorted(ROOT.glob("rtl/*.sv"))]
    if simulator == "icarus":
        binary = directory/"simulation.vvp"
        execute(["iverilog","-g2012","-Wall","-s","top_csr_tb","-o",relative(binary),
                 *sources,"tests/top_csr_tb.sv"],directory,"compile",["iverilog","-V"])
        argv = ["vvp",relative(binary)]
        version = ["iverilog","-V"]
    else:
        objects = directory/"compile-obj"
        execute(["verilator","--binary","--timing","-Wno-fatal","-j","2",
                 "--top-module","top_csr_tb","--Mdir",relative(objects),
                 *sources,"tests/top_csr_tb.sv"],directory,"compile",["verilator","--version"])
        argv = [relative(objects/"Vtop_csr_tb")]
        version = ["verilator","--version"]
    text = execute([*argv,f"+vectors={relative(vectors)}"],directory,"simulation",version)
    summary = re.search(r"SUMMARY top_csr comparisons=(\d+) held_edges=(\d+) "
                        r"reset_canceled_responses=1",text)
    if not summary or int(summary[1]) != len(rows)+1 or int(summary[2]) != 4*(len(rows)+1):
        raise AssertionError("incomplete compact integrated CSR observation counts")
    return dict(status="passed", comparisons=int(summary[1]), raw_summary=summary[0])


def parameter_case(directory, parameters, invalid=False):
    sources = [relative(p) for p in sorted(ROOT.glob("rtl/*.sv"))]
    if invalid:
        binary = directory/"simulation.vvp"
        execute(["iverilog","-g2012","-Wall","-s","top_csr_tb",
                 *[f"-Ptop_csr_tb.{key}={value}" for key,value in parameters.items()],
                 "-o",relative(binary),*sources,"tests/top_csr_tb.sv"],
                directory,"compile",["iverilog","-V"])
        try:
            execute(["vvp",relative(binary)],directory,"rejection",["iverilog","-V"])
        except RuntimeError:
            receipt = json.loads((directory/"rejection.receipt.json").read_text())
            text = (directory/"rejection.stdout.txt").read_text()
            if receipt["exit"] not in (None,0) and not receipt["timed_out"] and "PARAMETER ERROR" in text:
                return dict(status="passed", invalid=True, diagnostic=text.strip())
            raise AssertionError("illegal parameter failed without executable PARAMETER ERROR")
        raise AssertionError("illegal parameter did not reject")
    execute(["verilator","--lint-only","--timing","-Wno-fatal","--top-module","top_csr_tb",
             *[f"-G{key}={value}" for key,value in parameters.items()],
             *sources,"tests/top_csr_tb.sv"],directory,"elaboration",["verilator","--version"])
    return dict(status="passed", invalid=False, coverage="source elaboration only")


def leaf_cases(output):
    results = []
    for leaf, base, invalids, extremes in (
        ("epilogue", dict(MAX_VECTOR=1, HEAD_DIM=2),
         [("MAX_VECTOR", 0), ("MAX_VECTOR", 4865), ("HEAD_DIM", 0),
          ("HEAD_DIM", 3), ("HEAD_DIM", 66)],
         [dict(MAX_VECTOR=4864, HEAD_DIM=64)]),
        ("attention", dict(NUM_Q_HEADS=1, NUM_KV_HEADS=1, HEAD_DIM=8,
                           MAX_SEQ_LEN=1, TILE_TOKENS=128),
         [("NUM_Q_HEADS", 0), ("NUM_Q_HEADS", 15), ("NUM_KV_HEADS", 0),
          ("NUM_KV_HEADS", 3), ("NUM_KV_HEADS", 2), ("HEAD_DIM", 0),
          ("HEAD_DIM", 3), ("HEAD_DIM", 66), ("MAX_SEQ_LEN", 0),
          ("MAX_SEQ_LEN", 32769), ("TILE_TOKENS", 0), ("TILE_TOKENS", 129)],
         [dict(NUM_Q_HEADS=14, NUM_KV_HEADS=2, HEAD_DIM=64,
               MAX_SEQ_LEN=32768, TILE_TOKENS=1),
          dict(NUM_Q_HEADS=3, NUM_KV_HEADS=1, HEAD_DIM=8,
               MAX_SEQ_LEN=17, TILE_TOKENS=3)])):
        jobs = [(base, False), *[(parameters, False) for parameters in extremes],
                *[({**base, parameter: bad}, True) for parameter, bad in invalids]]
        for parameters, invalid in jobs:
            directory = output/f"leaf-{leaf}-{uuid.uuid4().hex[:8]}"
            directory.mkdir()
            top = leaf+"_parameter_tb"
            binary = directory/"simulation.vvp"
            try:
                execute(["iverilog", "-g2012", "-Wall", "-s", top,
                         *[f"-P{top}.{key}={value}" for key, value in parameters.items()],
                         "-o", relative(binary),
                         *[relative(p) for p in sorted(ROOT.glob("rtl/*.sv"))],
                         "tests/parameter_leaf_tb.sv"], directory, "compile", ["iverilog", "-V"])
                try:
                    text = execute(["vvp", relative(binary)], directory, "simulation",
                                   ["iverilog", "-V"])
                except RuntimeError:
                    receipt = json.loads((directory/"simulation.receipt.json").read_text())
                    text = (directory/"simulation.stdout.txt").read_text()
                    if (not invalid or receipt["exit"] in (None, 0) or receipt["timed_out"]
                            or "PARAMETER ERROR" not in text):
                        raise
                else:
                    if invalid or f"SUMMARY legal {leaf} parameter elaboration" not in text:
                        raise AssertionError("missing explicit parameter acceptance/rejection")
                row = dict(status="passed", diagnostic=text.strip(),
                           coverage="explicit rejection" if invalid else "elaboration only")
            except (RuntimeError, AssertionError) as exc:
                row = dict(status="failed", error=str(exc))
            results.append(dict(id=f"leaf-{leaf}", parameters=parameters, invalid=invalid,
                                path=relative(directory), **row))
    return results


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True)
    parser.add_argument("--diagnostic", action="store_true")
    parser.add_argument("--leaf-only", action="store_true")
    args = parser.parse_args()
    output = ROOT/args.output
    output.mkdir(parents=True,exist_ok=False)
    receipt = dict(argv=["python3","tests/run_parameters.py",*sys.argv[1:]],cwd=".",
                   start=timestamp(),timeout=remaining(),source_sha256=hashes(),tool_version=sys.version)
    results = []
    abi_hash = check_abi()
    jobs = [] if args.leaf_only else [("compact-csr-icarus",None,False)]
    if not args.diagnostic and not args.leaf_only:
        jobs += [("compact-csr-verilator",None,False),
                 ("smallest",SMALL,False),("nonpower",NONPOWER,False),("default",DEFAULT,False)]
        for parameter,bad in (("NUM_LAYERS",0),("NUM_LAYERS",25),("HIDDEN_SIZE",0),
                              ("HIDDEN_SIZE",904),("INTERMEDIATE_SIZE",0),
                              ("INTERMEDIATE_SIZE",4872),("HEAD_DIM",7),
                              ("HEAD_DIM",66),("GROUP_SIZE",0),("GROUP_SIZE",3),
                              ("NUM_Q_HEADS",3),("NUM_KV_HEADS",0),("NUM_KV_HEADS",2),
                              ("AWQ_BITS",8),("VOCAB_SIZE",0),("VOCAB_SIZE",151937),
                              ("MAX_SEQ_LEN",0),("MAX_SEQ_LEN",32769),
                              ("LANES",32),("BANKS",4),("LANES_PER_BANK",4),
                              ("DDR_WIDTH",256),("TILE_BEATS",0),("TILE_BEATS",257),
                              ("KV_WINDOW",0),("KV_WINDOW",2),("FLASH_TILE",0),("FLASH_TILE",129)):
            jobs.append((f"illegal-{parameter}-{bad}",{**SMALL,parameter:bad},True))
    for name,parameters,invalid in jobs:
        directory = output/f"{name}-{uuid.uuid4().hex[:8]}"
        directory.mkdir()
        try:
            row = (compact_smoke(directory,"icarus" if "icarus" in name else "verilator")
                   if parameters is None else parameter_case(directory,parameters,invalid))
        except (RuntimeError,AssertionError) as exc:
            row = dict(status="failed",error=str(exc))
        results.append(dict(id=name,path=relative(directory),parameters=parameters,**row))
    if not args.diagnostic:
        results.extend(leaf_cases(output))
    result = dict(status="passed" if all(r["status"]=="passed" for r in results) else "failed",
                  runs=results,ordered_port_sha256=abi_hash,diagnostic=args.diagnostic,
                  coverage_limits=["TILE_BEATS/KV_WINDOW/FLASH_TILE legal cross matrix"]
                  if not args.leaf_only else [])
    with (output/"result.json").open("x") as out:
        json.dump(result,out,indent=2)
    receipt.update(exit=0 if result["status"]=="passed" else 1,end=timestamp(),
                   timed_out=remaining()<=0,result=relative(output/"result.json"))
    with (output/"receipt.json").open("x") as out:
        json.dump(receipt,out,indent=2)
    print(json.dumps(result),flush=True)
    return receipt["exit"]


if __name__=="__main__":
    raise SystemExit(main())
