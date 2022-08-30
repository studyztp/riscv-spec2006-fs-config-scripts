import os
import argparse
import m5
from xmlrpc.client import MAXINT
from gem5.components.boards.riscv_board import RiscvBoard
from gem5.components.cachehierarchies.classic.private_l1_private_l2_cache_hierarchy import (
    PrivateL1PrivateL2CacheHierarchy,
)
from gem5.components.memory import DualChannelDDR4_2400, SingleChannelDDR4_2400
from gem5.components.processors.cpu_types import CPUTypes
from gem5.components.processors.simple_processor import SimpleProcessor
from gem5.utils.simpoint import SimPoint
from gem5.isas import ISA
from gem5.resources.resource import CustomDiskImageResource, Resource
from gem5.simulate.exit_event import ExitEvent
from gem5.simulate.simulator import Simulator
from m5.stats import dump, reset
from pathlib import Path

from gem5.components.processors.simple_switchable_processor import (
    SimpleSwitchableProcessor,
)
import time
from m5.util import warn

# Build errors: 416.gamess(base), 447.dealII(base), 450.soplex(base),
# 483.xalancbmk(base)
# Build successes: 400.perlbench(base), 401.bzip2(base), 403.gcc(base),
# 410.bwaves(base), 429.mcf(base), 433.milc(base), 434.zeusmp(base),
# 435.gromacs(base), 436.cactusADM(base), 437.leslie3d(base), 444.namd(base),
# 445.gobmk(base), 453.povray(base), 454.calculix(base), 456.hmmer(base),
# 458.sjeng(base), 459.GemsFDTD(base), 462.libquantum(base), 464.h264ref(base),
# 465.tonto(base), 470.lbm(base), 471.omnetpp(base), 473.astar(base),
# 481.wrf(base), 482.sphinx3(base), 998.specrand(base), 999.specrand(base)

benchmark_choices = [
    "400.perlbench",
    "401.bzip2",
    "403.gcc",
    "410.bwaves",
    "429.mcf",
    "433.milc",
    "434.zeusmp",
    "435.gromacs",
    "436.cactusADM",
    "437.leslie3d",
    "444.namd",
    "445.gobmk",
    "453.povray",
    "454.calculix",
    "456.hmmer",
    "458.sjeng",
    "459.GemsFDTD",
    "462.libquantum",
    "464.h264ref",
    "465.tonto",
    "470.lbm",
    "471.omnetpp",
    "473.astar",
    "481.wrf",
    "482.sphinx3",
    "998.specrand",
    "999.specrand",
]

size_choices = ["test", "train", "ref"]

parser = argparse.ArgumentParser(
    description="An example configuration script to run the \
        SPEC CPU2006 benchmarks."
)

parser.add_argument(
    "--benchmark",
    type=str,
    required=True,
    help="Input the benchmark program to execute.",
    choices=benchmark_choices,
)

parser.add_argument(
    "--size",
    type=str,
    required=True,
    help="Sumulation size the benchmark program.",
    choices=size_choices,
)

parser.add_argument(
    "--checkpoint_dir",
    type=str,
    required=True,
    help="Where to save the checkpoint.",
)


args = parser.parse_args()

output_dir = "speclogs_" + "".join(x.strip() for x in time.asctime().split())
output_dir = output_dir.replace(":", "")

try:
    os.makedirs(os.path.join(m5.options.outdir, output_dir))
except FileExistsError:
    warn("output directory already exists!")

cache_hierarchy = PrivateL1PrivateL2CacheHierarchy(
    l1d_size="32kB",
    l1i_size="32kB",
    l2_size="256kB",
)

memory = SingleChannelDDR4_2400()

processor = SimpleProcessor(
    cpu_type=CPUTypes.ATOMIC,
    num_cores=1,
    isa=ISA.RISCV,
)

board = RiscvBoard(
    clk_freq="3GHz",
    processor=processor,
    memory=memory,
    cache_hierarchy=cache_hierarchy,
)

command = "{} {} {}".format(args.benchmark, args.size, output_dir)

board.set_kernel_disk_workload(
    kernel=Resource(
        "riscv-bootloader-vmlinux-5.10",
    ),
    disk_image=CustomDiskImageResource(
        os.path.join(
            os.path.expanduser("~"),
            "/home/studyztp/data/SPEC2006-riscv-test/benchmarks/disk/riscv64-ubuntu-SPEC2006.img",
        ),
        disk_root_partition="1",
    ),
    readfile_contents=command,
)

dir = Path(args.checkpoint_dir)
dir.mkdir(exist_ok=True)


def take_checkpoint():
    while True:
        m5.checkpoint((dir).as_posix())
        yield True


simulator = Simulator(
    full_system=True,
    board=board,
    on_exit_event={ExitEvent.EXIT: take_checkpoint()},
)

simulator.run()
