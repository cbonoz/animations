"""Liquid/sand particle simulation with Pygame + video export with audio."""

import pygame
import numpy as np
import imageio
from pathlib import Path
import math
import subprocess
import wave


class LiquidSimulation:
    """Physics-based liquid/sand particle simulation with video export."""

    def __init__(self, width=800, height=800, fps=60, duration=15, particle_count=500):
        self.width = width
        self.height = height
        self.fps = fps
        self.duration = duration
        self.frames = []
        self.particle_count = particle_count

        # Initialize pygame
        pygame.init()
        self.display = pygame.display.set_mode((width, height))
        pygame.display.set_caption("Liquid Simulation")
        self.frame_number = 0

        # Physics state
        self.gravity = 0.2
        self.damping = 0.98
        self.particle_radius = 3

        # Particle system
        self.particles = self._init_particles()

        # Collision tracking
        self.collision_count = 0
        self.collision_times = []
        self.notes = [261.63, 293.66, 329.63, 349.23, 392.00, 440.00, 493.88, 523.25]

        # Barriers (walls)
        self.barriers = self._init_barriers()

    def _init_particles(self):
        """Initialize particles in a loose cluster."""
        particles = []
        cluster_center = np.array([self.width / 2, self.height / 4])
        cluster_radius = 80

        for _ in range(self.particle_count):
            # Random position in cluster
            angle = np.random.uniform(0, 2 * np.pi)
            r = np.random.uniform(0, cluster_radius)
            pos = cluster_center + np.array([r * np.cos(angle), r * np.sin(angle)])

            # Small random velocity
            vel = np.array([
                np.random.uniform(-1, 1),
                np.random.uniform(-0.5, 0.5)
            ])

            # Random color (warm colors for liquid)
            color = (
                np.random.randint(100, 255),
                np.random.randint(50, 200),
                np.random.randint(50, 150)
            )

            particles.append({
                'pos': pos,
                'vel': vel,
                'color': color,
                'mass': 1.0
            })

        return particles

    def _init_barriers(self):
        """Define barrier walls (ground and sides)."""
        return [
            # Ground
            {'x1': -50, 'y1': self.height - 20, 'x2': self.width + 50, 'y2': self.height - 20},
            # Left wall
            {'x1': 20, 'y1': -50, 'x2': 20, 'y2': self.height + 50},
            # Right wall
            {'x1': self.width - 20, 'y1': -50, 'x2': self.width - 20, 'y2': self.height + 50},
        ]

    def check_barrier_collision(self, particle):
        """Check and handle collision with barriers."""
        pos = particle['pos']
        vel = particle['vel']
        r = self.particle_radius

        for barrier in self.barriers:
            x1, y1, x2, y2 = barrier['x1'], barrier['y1'], barrier['x2'], barrier['y2']

            # Vector along barrier
            bx, by = x2 - x1, y2 - y1
            blen = math.sqrt(bx**2 + by**2)

            # Vector from barrier start to particle
            px, py = pos[0] - x1, pos[1] - y1

            # Project particle onto barrier
            t = max(0, min(1, (px * bx + py * by) / (blen**2 + 0.0001)))
            closest_x = x1 + t * bx
            closest_y = y1 + t * by

            # Distance to barrier
            dist_x = pos[0] - closest_x
            dist_y = pos[1] - closest_y
            dist = math.sqrt(dist_x**2 + dist_y**2)

            if dist < r:
                # Collision!
                normal_x = dist_x / (dist + 0.0001)
                normal_y = dist_y / (dist + 0.0001)

                # Reflect velocity
                dot = vel[0] * normal_x + vel[1] * normal_y
                if dot < 0:
                    particle['vel'][0] = (vel[0] - 2 * dot * normal_x) * self.damping
                    particle['vel'][1] = (vel[1] - 2 * dot * normal_y) * self.damping

                    # Push out of barrier
                    particle['pos'][0] += normal_x * (r - dist)
                    particle['pos'][1] += normal_y * (r - dist)

                    self.collision_count += 1
                    self.play_note()

    def check_particle_collision(self, p1, p2):
        """Check if two particles collide and handle it."""
        diff = p2['pos'] - p1['pos']
        dist = np.linalg.norm(diff)
        min_dist = 2 * self.particle_radius

        if dist < min_dist and dist > 0.01:
            # Normal vector
            normal = diff / dist

            # Relative velocity
            rel_vel = p2['vel'] - p1['vel']
            vel_along_normal = np.dot(rel_vel, normal)

            # Don't collide if moving apart
            if vel_along_normal < 0:
                # Impulse
                impulse = vel_along_normal / 2
                p1['vel'] += impulse * normal
                p2['vel'] -= impulse * normal

                # Separate particles
                overlap = min_dist - dist
                p1['pos'] -= normal * overlap / 2
                p2['pos'] += normal * overlap / 2

    def update_physics(self):
        """Update particle simulation."""
        # Apply gravity
        for p in self.particles:
            p['vel'][1] += self.gravity

        # Update positions
        for p in self.particles:
            p['pos'] += p['vel']

        # Barrier collisions
        for p in self.particles:
            self.check_barrier_collision(p)

        # Particle-particle collisions using spatial grid (much faster)
        grid_size = self.particle_radius * 8  # Larger cells for faster lookup
        grid = {}
        
        # Build grid
        for i, p in enumerate(self.particles):
            cell = (int(p['pos'][0] / grid_size), int(p['pos'][1] / grid_size))
            if cell not in grid:
                grid[cell] = []
            grid[cell].append(i)
        
        # Check collisions only with nearby particles (limit checks per particle)
        max_checks = 50  # Cap collision checks to prevent slowdown
        for cell_key, indices in grid.items():
            cx, cy = cell_key
            check_count = 0
            
            # Check particles in this cell and immediate neighbors
            for nx in [cx, cx + 1]:  # Only check right and down to avoid duplicates
                for ny in [cy, cy + 1]:
                    neighbor_key = (nx, ny)
                    if neighbor_key in grid:
                        for i in indices:
                            for j in grid[neighbor_key]:
                                if i < j and check_count < max_checks:
                                    self.check_particle_collision(self.particles[i], self.particles[j])
                                    check_count += 1
                                    if check_count >= max_checks:
                                        break

    def play_note(self):
        """Record collision for audio."""
        self.collision_times.append(self.frame_number / self.fps)

    def draw(self, surface):
        """Draw particles."""
        surface.fill((10, 10, 20))  # Dark background

        # Draw barriers
        for barrier in self.barriers:
            pygame.draw.line(
                surface,
                (200, 200, 200),
                (barrier['x1'], barrier['y1']),
                (barrier['x2'], barrier['y2']),
                2
            )

        # Draw particles
        for p in self.particles:
            pygame.draw.circle(
                surface,
                p['color'],
                p['pos'].astype(int),
                self.particle_radius
            )

        # Draw counters
        font = pygame.font.Font(None, 36)
        text = font.render(f"Particles: {len(self.particles)}", True, (255, 255, 255))
        surface.blit(text, (10, 10))
        text = font.render(f"Collisions: {self.collision_count}", True, (255, 255, 255))
        surface.blit(text, (10, 50))

    def capture_frame(self):
        """Capture current frame as numpy array."""
        frame = pygame.surfarray.array3d(self.display)
        frame = np.transpose(frame, (1, 0, 2))
        frame = np.flip(frame, axis=2)  # BGR to RGB
        return frame.astype(np.uint8)

    def run(self):
        """Run simulation and record video."""
        clock = pygame.time.Clock()
        frame_count = 0
        total_frames = self.fps * self.duration

        print(f"Recording {self.duration}s liquid simulation at {self.fps} FPS...")
        print(f"Simulating {self.particle_count} particles...")

        while frame_count < total_frames:
            self.frame_number = frame_count

            # Update
            self.update_physics()

            # Draw
            self.draw(self.display)
            pygame.display.flip()

            # Capture frame
            frame = self.capture_frame()
            self.frames.append(frame)

            frame_count += 1
            clock.tick(self.fps)

            if frame_count % 30 == 0:
                print(f"  {frame_count}/{total_frames} frames ({100*frame_count/total_frames:.1f}%)")

        print("Recording complete! Encoding video...")
        self.generate_audio_track()
        self.save_video()
        pygame.quit()

    def generate_audio_track(self):
        """Generate audio track from collision times."""
        sample_rate = 44100
        total_samples = int(self.duration * sample_rate)
        audio_data = np.zeros(total_samples, dtype=np.int16)

        print("Generating audio track...")

        for collision_time in self.collision_times:
            note_idx = len([t for t in self.collision_times if t <= collision_time]) - 1
            note_freq = self.notes[note_idx % len(self.notes)]

            # Shorter note duration for particle collisions
            note_duration = 0.05
            note_samples = int(note_duration * sample_rate)
            start_sample = int(collision_time * sample_rate)
            end_sample = min(start_sample + note_samples, total_samples)

            # Generate sine wave
            t = np.arange(end_sample - start_sample) / sample_rate
            waveform = np.sin(2 * np.pi * note_freq * t)

            # Apply envelope
            envelope_samples = min(500, len(waveform) // 2)
            for i in range(envelope_samples):
                waveform[i] *= i / envelope_samples
                if len(waveform) - i - 1 >= 0:
                    waveform[-(i+1)] *= i / envelope_samples

            # Mix into audio track
            audio_data[start_sample:end_sample] = np.int16(waveform * 32767 * 0.2)

        # Save audio to file
        audio_path = Path("media/videos/liquid_audio.wav")
        audio_path.parent.mkdir(parents=True, exist_ok=True)

        with wave.open(str(audio_path), 'w') as wav_file:
            wav_file.setnchannels(1)
            wav_file.setsampwidth(2)
            wav_file.setframerate(sample_rate)
            wav_file.writeframes(audio_data.tobytes())

        self.audio_path = audio_path

    def save_video(self):
        """Save frames to MP4 video with audio."""
        output_path = Path("media/videos/liquid_simulation.mp4")
        output_path.parent.mkdir(parents=True, exist_ok=True)
        temp_video = Path("media/videos/liquid_temp.mp4")

        try:
            # Save video without audio first
            print("Encoding video frames...")
            writer = imageio.get_writer(str(temp_video), fps=self.fps, codec='libx264')
            for frame in self.frames:
                writer.append_data(frame)
            writer.close()

            # Combine video and audio with ffmpeg
            print("Mixing audio with video...")
            cmd = [
                "ffmpeg",
                "-i", str(temp_video),
                "-i", str(self.audio_path),
                "-c:v", "copy",
                "-c:a", "aac",
                "-map", "0:v:0",
                "-map", "1:a:0",
                "-shortest",
                "-y",
                str(output_path)
            ]
            result = subprocess.run(cmd, capture_output=True, text=True, check=False)
            if result.returncode != 0:
                raise RuntimeError(f"FFmpeg failed: {result.stderr}")
            # Clean up temp files
            temp_video.unlink()
            self.audio_path.unlink()

        except Exception as e:
            print(f"Error: {e}")
            print("Saving video without audio...")
            if temp_video.exists():
                import shutil
                shutil.copy(str(temp_video), str(output_path))
                temp_video.unlink()

        print(f"✓ Video saved to {output_path}")


if __name__ == "__main__":
    sim = LiquidSimulation(width=800, height=800, fps=60, duration=15, particle_count=500)
    sim.run()
