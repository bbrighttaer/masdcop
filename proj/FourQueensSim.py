# Author: bbrighttaer
# Project: masdcop
# Date: 5/18/2021
# Time: 4:04 PM
# File: FourQueensSim.py

import argparse

from masdcop.env import FourQueens

if __name__ == '__main__':
    parser = argparse.ArgumentParser('Four Queens DCSP Simulation')
    parser.add_argument('--num_agents', '-n', help='Number of agents',
                        type=int, default=4)
    args = parser.parse_args()

    sim = FourQueens(args.num_agents)
    sim.resolve()
    sol = sim.algo.sol
    print(sol)