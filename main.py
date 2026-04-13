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
        # TODO: Liquid/sand particle simulation with gravity and collisions
        # TODO: Particle swarm with physics
        # TODO: N-body gravity simulation
        # TODO: Magnetic particle attraction/repulsion
        # TODO: Conway's Game of Life
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
        duration=args.duration,
        num_balls=args.num_balls,
        num_walls=args.num_walls,
        respawn_interval=args.respawn_interval
    )
    # Set custom rotation speed if provided
    if args.rotation_speed is not None:
        anim.rotation_speed = args.rotation_speed
    
    # Set wall health options
    if args.invincible_walls:
        anim.wall_health = float('inf')
    elif args.wall_health is not None:
        anim.wall_health = args.wall_health
    
    anim.run()
    print(f"✓ Video saved to media/videos/bouncing_ball.mp4")


def main():
    parser = argparse.ArgumentParser(
        description="Generate viral simulation videos",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py --type bouncing --duration 20
  python main.py --type bouncing --num-balls 3 --num-walls 2
  python main.py --type bouncing --num-balls 5 --respawn-interval 2
  python main.py --type bouncing --rotation-speed 2.0  # Fast rotation
  python main.py --type bouncing --rotation-speed 0 --num-balls 4  # No rotation
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
    parser.add_argument(
        "--num-balls",
        type=int,
        default=1,
        help="Number of balls to spawn (default: 1)"
    )
    parser.add_argument(
        "--num-walls",
        type=int,
        default=1,
        help="Number of wall layers (1-3, default: 1)"
    )
    parser.add_argument(
        "--respawn-interval",
        type=float,
        default=3,
        help="Seconds between ball respawns (default: 3)"
    )
    parser.add_argument(
        "--rotation-speed",
        type=float,
        help="Barrier rotation speed in degrees/frame (default: 0.5, use 0 for no rotation)"
    )
    parser.add_argument(
        "--wall-health",
        type=int,
        default=None,
        help="Barrier health per segment (default: 80/60/40 based on walls, None=infinite)"
    )
    parser.add_argument(
        "--invincible-walls",
        action="store_true",
        help="Make walls indestructible (infinite health)"
    )
    
    args = parser.parse_args()
    
    # Validate parameters
    if args.duration < 15 or args.duration > 30:
        print("Error: Duration must be between 15 and 30 seconds")
        sys.exit(1)
    
    if args.num_balls < 1:
        print("Error: num_balls must be >= 1")
        sys.exit(1)
    
    if args.num_walls < 1 or args.num_walls > 3:
        print("Error: num_walls must be between 1 and 3")
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



