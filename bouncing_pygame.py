"""Bouncing ball animation with destructible barriers using Pygame + video export with audio."""

import pygame
import numpy as np
import imageio
from pathlib import Path
import math
import subprocess
import wave


class Ball:
    """Individual ball for the simulation."""
    
    def __init__(self, pos, vel, radius=15):
        self.pos = np.array(pos, dtype=float)
        self.vel = np.array(vel, dtype=float)
        self.radius = radius
        self.color = (255, 50, 50)
        self.alive = True


class Barrier:
    """Destructible barrier."""
    
    def __init__(self, x1, y1, x2, y2, max_health=100):
        self.x1 = x1
        self.y1 = y1
        self.x2 = x2
        self.y2 = y2
        self.max_health = max_health
        self.health = max_health
        self.length = math.sqrt((x2 - x1)**2 + (y2 - y1)**2)
    
    def take_damage(self, amount=1):
        """Damage the barrier."""
        self.health = max(0, self.health - amount)
        return self.health <= 0
    
    def get_color(self):
        """Color based on health."""
        ratio = self.health / self.max_health
        if ratio > 0.66:
            return (100, 149, 237)  # Blue
        elif ratio > 0.33:
            return (255, 165, 0)    # Orange
        else:
            return (255, 50, 50)    # Red


class BouncingBallAnimation:
    """Physics-based bouncing ball in barriers with damage system and video export."""

    def __init__(self, width=800, height=800, fps=60, duration=15, 
                 num_balls=1, num_walls=1, respawn_interval=3):
        self.width = width
        self.height = height
        self.fps = fps
        self.duration = duration
        self.frames = []
        self.num_walls = num_walls
        self.respawn_interval = respawn_interval

        # Initialize pygame
        pygame.init()
        self.display = pygame.display.set_mode((width, height))
        pygame.display.set_caption("Bouncing Ball - Destructible Barriers")
        self.frame_number = 0

        # Physics parameters
        self.gravity = 0.15
        self.damping = 0.92

        # Barriers
        self.barriers = self._init_barriers()

        # Balls
        self.balls = []
        self.next_respawn_time = 0
        self.balls_spawned = 0
        self.num_balls_to_spawn = num_balls

        # Spawn initial balls
        for i in range(num_balls):
            self._spawn_ball()

        # Collision tracking
        self.collision_count = 0
        self.collision_times = []
        self.notes = [261.63, 293.66, 329.63, 349.23, 392.00, 440.00, 493.88, 523.25]

    def _init_barriers(self):
        """Initialize destructible barriers."""
        barriers = []
        center_x, center_y = self.width / 2, self.height / 2
        
        if self.num_walls == 1:
            # Single rotating square
            barrier_size = 300
            corners = [
                (center_x - barrier_size, center_y - barrier_size),
                (center_x + barrier_size, center_y - barrier_size),
                (center_x + barrier_size, center_y + barrier_size),
                (center_x - barrier_size, center_y + barrier_size),
            ]
            for i in range(4):
                x1, y1 = corners[i]
                x2, y2 = corners[(i + 1) % 4]
                barriers.append(Barrier(x1, y1, x2, y2, max_health=80))
        
        elif self.num_walls == 2:
            # Two concentric squares
            for barrier_size in [200, 350]:
                corners = [
                    (center_x - barrier_size, center_y - barrier_size),
                    (center_x + barrier_size, center_y - barrier_size),
                    (center_x + barrier_size, center_y + barrier_size),
                    (center_x - barrier_size, center_y + barrier_size),
                ]
                for i in range(4):
                    x1, y1 = corners[i]
                    x2, y2 = corners[(i + 1) % 4]
                    barriers.append(Barrier(x1, y1, x2, y2, max_health=60))
        
        else:  # 3+ walls
            # Three concentric squares
            for barrier_size in [150, 250, 350]:
                corners = [
                    (center_x - barrier_size, center_y - barrier_size),
                    (center_x + barrier_size, center_y - barrier_size),
                    (center_x + barrier_size, center_y + barrier_size),
                    (center_x - barrier_size, center_y + barrier_size),
                ]
                for i in range(4):
                    x1, y1 = corners[i]
                    x2, y2 = corners[(i + 1) % 4]
                    barriers.append(Barrier(x1, y1, x2, y2, max_health=50))
        
        return barriers

    def _spawn_ball(self):
        """Spawn a new ball at random location."""
        center_x, center_y = self.width / 2, self.height / 2
        
        # Random position near center
        angle = np.random.uniform(0, 2 * np.pi)
        r = np.random.uniform(50, 100)
        pos = [center_x + r * np.cos(angle), center_y + r * np.sin(angle)]
        
        # Random velocity
        vel = [np.random.uniform(-3, 3), np.random.uniform(-2, 1)]
        
        self.balls.append(Ball(pos, vel, radius=12))
        self.balls_spawned += 1

    def check_ball_barrier_collision(self, ball):
        """Check ball collision with barriers."""
        for barrier in self.barriers:
            if barrier.health <= 0:
                continue  # Skip destroyed barriers
            
            x1, y1, x2, y2 = barrier.x1, barrier.y1, barrier.x2, barrier.y2
            
            # Vector along barrier
            bx, by = x2 - x1, y2 - y1
            blen = math.sqrt(bx**2 + by**2)
            
            # Vector from barrier start to ball
            px, py = ball.pos[0] - x1, ball.pos[1] - y1
            
            # Project ball onto barrier
            t = max(0, min(1, (px * bx + py * by) / (blen**2 + 0.0001)))
            closest_x = x1 + t * bx
            closest_y = y1 + t * by
            
            # Distance to barrier
            dist_x = ball.pos[0] - closest_x
            dist_y = ball.pos[1] - closest_y
            dist = math.sqrt(dist_x**2 + dist_y**2)
            
            if dist < ball.radius:
                # Collision!
                normal_x = dist_x / (dist + 0.0001)
                normal_y = dist_y / (dist + 0.0001)
                
                # Reflect velocity
                dot = ball.vel[0] * normal_x + ball.vel[1] * normal_y
                if dot < 0:  # Moving toward wall
                    ball.vel[0] = (ball.vel[0] - 2 * dot * normal_x) * self.damping
                    ball.vel[1] = (ball.vel[1] - 2 * dot * normal_y) * self.damping
                    
                    # Push out of wall
                    ball.pos[0] += normal_x * (ball.radius - dist)
                    ball.pos[1] += normal_y * (ball.radius - dist)
                    
                    # Damage barrier
                    if barrier.take_damage(1):
                        pass  # Barrier destroyed
                    
                    self.collision_count += 1
                    self.play_note()

    def check_ball_ball_collision(self, b1, b2):
        """Check if two balls collide and handle it."""
        diff = b2.pos - b1.pos
        dist = np.linalg.norm(diff)
        min_dist = 2 * b1.radius
        
        if dist < min_dist and dist > 0.01:
            normal = diff / dist
            rel_vel = b2.vel - b1.vel
            vel_along_normal = np.dot(rel_vel, normal)
            
            if vel_along_normal < 0:
                impulse = vel_along_normal / 2
                b1.vel += impulse * normal
                b2.vel -= impulse * normal
                
                overlap = min_dist - dist
                b1.pos -= normal * overlap / 2
                b2.pos += normal * overlap / 2

    def play_note(self):
        """Record collision for audio."""
        self.collision_times.append(self.frame_number / self.fps)

    def update_physics(self):
        """Update ball simulation."""
        # Handle respawning
        current_time = self.frame_number / self.fps
        if (self.balls_spawned < self.num_balls_to_spawn and 
            current_time >= self.next_respawn_time):
            self._spawn_ball()
            self.next_respawn_time = current_time + self.respawn_interval
        
        # Update each ball
        for ball in self.balls:
            if not ball.alive:
                continue
            
            # Apply gravity
            ball.vel[1] += self.gravity
            ball.pos += ball.vel
            
            # Barrier collisions
            self.check_ball_barrier_collision(ball)
            
            # Hard bounds (escape detection)
            if (ball.pos[0] < -50 or ball.pos[0] > self.width + 50 or
                ball.pos[1] < -50 or ball.pos[1] > self.height + 50):
                ball.alive = False
        
        # Ball-ball collisions (only for alive balls)
        alive_balls = [b for b in self.balls if b.alive]
        for i in range(len(alive_balls)):
            for j in range(i + 1, len(alive_balls)):
                self.check_ball_ball_collision(alive_balls[i], alive_balls[j])

    def draw(self, surface):
        """Draw scene."""
        surface.fill((10, 10, 20))
        
        # Draw barriers
        for barrier in self.barriers:
            if barrier.health > 0:
                color = barrier.get_color()
                pygame.draw.line(surface, color, (barrier.x1, barrier.y1), 
                               (barrier.x2, barrier.y2), 3)
                
                # Draw health indicator
                health_ratio = barrier.health / barrier.max_health
                indicator_color = (100 + health_ratio * 155, 
                                 max(0, 150 - health_ratio * 150), 50)
                pygame.draw.line(surface, indicator_color, (barrier.x1, barrier.y1),
                               (barrier.x2, barrier.y2), 1)
        
        # Draw balls
        for ball in self.balls:
            if ball.alive:
                pygame.draw.circle(surface, ball.color, ball.pos.astype(int), ball.radius)
        
        # Draw stats
        font = pygame.font.Font(None, 32)
        
        # Countdown timer
        remaining_time = self.duration - (self.frame_number / self.fps)
        timer_text = font.render(f"Time: {remaining_time:.1f}s", True, (255, 255, 255))
        surface.blit(timer_text, (10, 10))
        
        # Collision counter
        collisions_text = font.render(f"Collisions: {self.collision_count}", True, (255, 255, 255))
        surface.blit(collisions_text, (10, 50))
        
        # Alive/escaped balls
        alive_count = sum(1 for b in self.balls if b.alive)
        escaped_count = sum(1 for b in self.balls if not b.alive)
        status_text = font.render(f"Balls: {alive_count} alive, {escaped_count} escaped", 
                                 True, (255, 200, 100))
        surface.blit(status_text, (10, 90))

    def capture_frame(self):
        """Capture current frame as numpy array."""
        frame = pygame.surfarray.array3d(self.display)
        frame = np.transpose(frame, (1, 0, 2))
        frame = np.flip(frame, axis=2)
        return frame.astype(np.uint8)

    def run(self):
        """Run simulation and record video."""
        clock = pygame.time.Clock()
        frame_count = 0
        total_frames = self.fps * self.duration

        print(f"Recording {self.duration}s animation at {self.fps} FPS...")
        print(f"Spawning {self.num_balls_to_spawn} balls with {self.num_walls} wall(s)...")

        while frame_count < total_frames:
            self.frame_number = frame_count

            self.update_physics()
            self.draw(self.display)
            pygame.display.flip()

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

            note_duration = 0.1
            note_samples = int(note_duration * sample_rate)
            start_sample = int(collision_time * sample_rate)
            end_sample = min(start_sample + note_samples, total_samples)

            t = np.arange(end_sample - start_sample) / sample_rate
            waveform = np.sin(2 * np.pi * note_freq * t)

            envelope_samples = min(1000, len(waveform) // 2)
            for i in range(envelope_samples):
                waveform[i] *= i / envelope_samples
                if len(waveform) - i - 1 >= 0:
                    waveform[-(i+1)] *= i / envelope_samples

            audio_data[start_sample:end_sample] = np.int16(waveform * 32767 * 0.3)

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
            print("Encoding video frames...")
            writer = imageio.get_writer(str(temp_video), fps=self.fps, codec='libx264')
            for frame in self.frames:
                writer.append_data(frame)
            writer.close()

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
    anim = BouncingBallAnimation(width=800, height=800, fps=60, duration=15, 
                                num_balls=2, num_walls=1, respawn_interval=5)
    anim.run()

