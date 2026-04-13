import subprocess
import sys


def run_bouncing_ball():
    """Run the bouncing ball animation with Pygame."""
    cmd = [sys.executable, "bouncing_pygame.py"]
    subprocess.run(cmd, check=True)


def main():
    print("Physics-Based Animations Project")
    print("-" * 40)
    print("Available animations:")
    print("  1. Bouncing Ball in Rotating Square")
    print("-" * 40)

    choice = input("Enter choice (1) or press Enter: ").strip() or "1"

    if choice in ["1", "bouncing"]:
        print("\nGenerating bouncing ball animation...")
        print("This will record a 15-second video with physics simulation.")
        run_bouncing_ball()
    else:
        print("Unknown choice")


if __name__ == "__main__":
    main()

