#!/usr/bin/env python3
"""CLI utility for generating viral simulation videos."""

import argparse
import sys
from pathlib import Path
from bouncing_pygame import BouncingBallAnimation


def list_simulations():
    """Print available simulation types."""
    simulations = {
        "bouncing": "Bouncing ball with gravity in a rotating square",
        # Future simulations:
        # "particles": "Particle swarm with physics",
        # "gravity": "N-body gravity simulation",
        # "magnetic": "Magnetic particle attraction/repulsion",
        # "cellular": "Conway's Game of Life",
        # "liquid": "Simple liquid/sand simulation",
    }
    print("\nAvailable simulations:")
    for name, desc in simulations.items():
        print(f"  {name:12} - {desc}")
    print()


def create_bouncing_simulation(args):
    """Create bouncing ball animation."""
    anim = BouncingBallAnimation(
        width=args.resolution,
        height=args.resolution,
        fps=args.fps,
        duration=args.duration
    )
    anim.run()
    print(f"✓ Video saved to media/videos/bouncing_ball.mp4")


def main():
    parser = argparse.ArgumentParser(
        description="Generate viral simulation videos",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py --type bouncing --duration 20
  python main.py --type bouncing --resolution 1024 --fps 60
  python main.py --list
        """
    )
    
    parser.add_argument(
        "--type",
        type=str,
        default="bouncing",
        help="Type of simulation (default: bouncing)"
    )
    parser.add_argument(
        "--duration",
        type=int,
        default=15,
        help="Video duration in seconds (15-30, default: 15)"
    )
    parser.add_argument(
        "--fps",
        type=int,
        default=60,
        help="Frames per second (default: 60)"
    )
    parser.add_argument(
        "--resolution",
        type=int,
        default=800,
        help="Video resolution (square, default: 800)"
    )
    parser.add_argument(
        "--list",
        action="store_true",
        help="List available simulations"
    )
    parser.add_argument(
        "--output",
        type=str,
        help="Output filename (default: simulation_type.mp4)"
    )
    
    args = parser.parse_args()
    
    # Validate duration
    if args.duration < 15 or args.duration > 30:
        print("Error: Duration must be between 15 and 30 seconds")
        sys.exit(1)
    
    # List simulations
    if args.list:
        list_simulations()
        sys.exit(0)
    
    # Run simulation
    if args.type == "bouncing":
        create_bouncing_simulation(args)
    else:
        print(f"Error: Unknown simulation type '{args.type}'")
        print("Use --list to see available simulations")
        sys.exit(1)


if __name__ == "__main__":
    main()

