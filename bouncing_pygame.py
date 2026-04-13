"""Bouncing ball animation with rotating square using Pygame + video export with audio."""

import pygame
import numpy as np
import imageio
from pathlib import Path
import math
import subprocess
import wave


class BouncingBallAnimation:
    """Physics-based bouncing ball in rotating square with video export."""

    def __init__(self, width=800, height=800, fps=60, duration=15):
        self.width = width
        self.height = height
        self.fps = fps
        self.duration = duration
        self.frames = []

        # Initialize pygame
        pygame.init()
        self.display = pygame.display.set_mode((width, height))
        pygame.display.set_caption("Bouncing Ball")
        self.frame_number = 0

        # Physics state
        self.ball_pos = np.array([200.0, 300.0])
        self.ball_vel = np.array([3.0, -1.0])
        self.ball_radius = 15
        self.gravity = 0.15
        self.damping = 0.92

        # Container (square)
        self.square_size = 400
        self.square_center = np.array([width / 2, height / 2])
        self.square_rotation = 0
        self.rotation_speed = 1.2  # degrees per frame

        # Collision tracking
        self.collision_count = 0
        self.collision_times = []  # Track when collisions occur
        self.notes = [261.63, 293.66, 329.63, 349.23, 392.00, 440.00, 493.88, 523.25]  # C to C octave

    def get_square_bounds(self):
        """Get rotated square bounds."""
        half_size = self.square_size / 2
        angle = math.radians(self.square_rotation)

        # Corners in local coordinates
        corners = [
            (-half_size, -half_size),
            (half_size, -half_size),
            (half_size, half_size),
            (-half_size, half_size),
        ]

        # Rotate and translate
        rotated = []
        for x, y in corners:
            rx = x * math.cos(angle) - y * math.sin(angle)
            ry = x * math.sin(angle) + y * math.cos(angle)
            rotated.append((rx + self.square_center[0], ry + self.square_center[1]))

        return rotated

    def check_collision_with_square(self):
        """Simple AABB-like collision detection."""
        corners = self.get_square_bounds()

        # Check distance to each edge
        for i in range(4):
            x1, y1 = corners[i]
            x2, y2 = corners[(i + 1) % 4]

            # Vector along edge
            edge_x, edge_y = x2 - x1, y2 - y1
            edge_len = math.sqrt(edge_x**2 + edge_y**2)

            # Vector from edge start to ball
            to_ball_x = self.ball_pos[0] - x1
            to_ball_y = self.ball_pos[1] - y1

            # Project ball onto edge
            t = max(0, min(1, (to_ball_x * edge_x + to_ball_y * edge_y) / (edge_len**2)))
            closest_x = x1 + t * edge_x
            closest_y = y1 + t * edge_y

            # Distance to edge
            dist_x = self.ball_pos[0] - closest_x
            dist_y = self.ball_pos[1] - closest_y
            dist = math.sqrt(dist_x**2 + dist_y**2)

            if dist < self.ball_radius:
                # Collision! Reflect velocity
                normal_x = dist_x / (dist + 0.0001)
                normal_y = dist_y / (dist + 0.0001)

                # Reflect
                dot = self.ball_vel[0] * normal_x + self.ball_vel[1] * normal_y
                if dot < 0:  # Moving toward wall
                    self.ball_vel[0] = (self.ball_vel[0] - 2 * dot * normal_x) * self.damping
                    self.ball_vel[1] = (self.ball_vel[1] - 2 * dot * normal_y) * self.damping

                    # Push out of wall
                    self.ball_pos[0] += normal_x * (self.ball_radius - dist)
                    self.ball_pos[1] += normal_y * (self.ball_radius - dist)

                    self.collision_count += 1
                    self.play_note()

    def play_note(self):
        """Record collision for later audio generation."""
        self.collision_times.append(self.frame_number / self.fps)
        self.collision_count += 1
    def update_physics(self):
        """Update ball position with gravity and bounds checking."""
        # Apply gravity
        self.ball_vel[1] += self.gravity

        # Update position
        self.ball_pos += self.ball_vel

        # Check collisions
        self.check_collision_with_square()

        # Safety: Hard bounds to prevent escape
        half_size = self.square_size / 2 - self.ball_radius - 5
        max_dist_from_center = half_size / math.sqrt(2)  # Diagonal distance
        
        dist_from_center = np.linalg.norm(self.ball_pos - self.square_center)
        if dist_from_center > max_dist_from_center:
            # Push ball back toward center
            direction = (self.square_center - self.ball_pos) / (dist_from_center + 0.0001)
            self.ball_pos = self.square_center - direction * max_dist_from_center
            # Dampen velocity when hitting hard boundary
            self.ball_vel *= 0.5

        # Rotate square
        self.square_rotation += self.rotation_speed
        self.square_rotation %= 360

    def draw(self, surface):
        """Draw scene."""
        surface.fill((20, 20, 30))  # Dark background

        # Draw rotating square
        corners = self.get_square_bounds()
        pygame.draw.polygon(surface, (100, 149, 237), corners, 3)  # Cornflower blue

        # Draw ball
        pygame.draw.circle(surface, (255, 50, 50), self.ball_pos.astype(int), self.ball_radius)

        # Draw collision counter
        font = pygame.font.Font(None, 36)
        text = font.render(f"Collisions: {self.collision_count}", True, (255, 255, 255))
        surface.blit(text, (10, 10))

    def capture_frame(self):
        """Capture current frame as numpy array."""
        frame = pygame.surfarray.array3d(self.display)
        frame = np.transpose(frame, (1, 0, 2))  # pygame uses (width, height, channels)
        frame = np.flip(frame, axis=2)  # BGR to RGB
        return frame.astype(np.uint8)

    def run(self):
        """Run simulation and record video."""
        clock = pygame.time.Clock()
        frame_count = 0
        total_frames = self.fps * self.duration

        print(f"Recording {self.duration}s animation at {self.fps} FPS...")

        while frame_count < total_frames:
            # Track frame for audio generation
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

            # Note duration (100ms)
            note_duration = 0.1
            note_samples = int(note_duration * sample_rate)
            start_sample = int(collision_time * sample_rate)
            end_sample = min(start_sample + note_samples, total_samples)

            # Generate sine wave
            t = np.arange(end_sample - start_sample) / sample_rate
            waveform = np.sin(2 * np.pi * note_freq * t)

            # Apply envelope (fade in/out for smooth sound)
            envelope_samples = min(1000, len(waveform) // 2)
            for i in range(envelope_samples):
                waveform[i] *= i / envelope_samples
                if len(waveform) - i - 1 >= 0:
                    waveform[-(i+1)] *= i / envelope_samples

            # Mix into audio track
            audio_data[start_sample:end_sample] = np.int16(waveform * 32767 * 0.3)

        # Save audio to file
        audio_path = Path("media/videos/collision_audio.wav")
        audio_path.parent.mkdir(parents=True, exist_ok=True)

        with wave.open(str(audio_path), 'w') as wav_file:
            wav_file.setnchannels(1)
            wav_file.setsampwidth(2)
            wav_file.setframerate(sample_rate)
            wav_file.writeframes(audio_data.tobytes())

        self.audio_path = audio_path

    def save_video(self):
        """Save frames to MP4 video with audio."""
        output_path = Path("media/videos/bouncing_ball.mp4")
        output_path.parent.mkdir(parents=True, exist_ok=True)
        temp_video = Path("media/videos/bouncing_ball_temp.mp4")

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
            temp_video.unlink()  # Remove temp video
            self.audio_path.unlink()  # Remove temp audio

        except Exception as e:
            print(f"Error: {e}")
            print("Saving video without audio...")
            if temp_video.exists():
                import shutil
                shutil.copy(str(temp_video), str(output_path))
                temp_video.unlink()

        print(f"✓ Video saved to {output_path}")


if __name__ == "__main__":
    # Create and run animation
    anim = BouncingBallAnimation(width=800, height=800, fps=60, duration=15)
    anim.run()
