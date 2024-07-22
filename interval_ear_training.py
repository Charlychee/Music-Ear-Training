import pygame
import pygame.midi
import random
from enum import StrEnum, Enum
from typing import Sequence
from dataclasses import dataclass

# Constants
TITLE = "Interval Ear Training"
SCREEN_WIDTH, SCREEN_HEIGHT = 640, 480
FONT_SIZE = 32
MARGIN = FONT_SIZE/2
MAX_ROUNDS = 10
FPS = 60
TIME_LIMIT = 5  # in seconds
DURATION = 1  # in seconds

TIME_LIMIT = int(TIME_LIMIT*1000)  # to milliseconds
DURATION = int(DURATION*1000)  # to milliseconds

# Mapping input to semitone interval
INPUTS = [pygame.K_s, pygame.K_e, pygame.K_d, pygame.K_r, pygame.K_f, pygame.K_g,
          pygame.K_y, pygame.K_h, pygame.K_u, pygame.K_j, pygame.K_i, pygame.K_k, pygame.K_l]
INPUTS = {key: idx for idx, key in enumerate(INPUTS)}

INTERVAL_NAME = ["P1", "m2", "M2", "m3", "M3",
                 "P4", "T", "P5", "m6", "M6", "m7", "M7", "P8"]


class GameState(StrEnum):
    ROUND_OVER = "round_over"
    PLAY_INTERVAL = "play"
    GUESS = "guess"
    GAME_OVER = "game_over"
    EXIT = "exit"


# Note Names
note_names = ["C", "Db", "D", "Eb", "E", "F", "Gb", "G", "Ab", "A", "Bb", "B"]
all_note_names = []
for num in range(10):
    all_note_names += [name + str(num) for name in note_names]

Note = Enum("Note", all_note_names, start=12)


@dataclass
class Interval:
    note1: Note
    note2: Note
    interval: int


# Initialize pygame and pygame.midi
pygame.init()
pygame.midi.init()
clock = pygame.time.Clock()

# Load image
keyboard_layout = pygame.image.load('keyboard-layout.png')
image_rect = keyboard_layout.get_rect()
image_rect.bottom = SCREEN_HEIGHT
image_rect.centerx = SCREEN_WIDTH // 2


# MIDI Setup
midi_out = pygame.midi.Output(0)
midi_out.set_instrument(0)  # Set to acoustic grand piano

def clear_event_buffer():
    for _ in pygame.event.get():
        pass

def play_midi_notes(notes: Sequence[Note], duration=1000):
    [midi_out.note_on(note.value, 127) for note in notes]
    pygame.time.wait(duration)
    [midi_out.note_off(note.value, 127) for note in notes]


def get_random_interval() -> Interval:
    note1 = random.randint(Note.C4.value, Note.C5.value)
    interval = random.randint(0, 12)
    return Interval(note1=Note(note1), interval=interval, note2=Note(note1+interval))


def play_melodic_interval(interval: Interval):
    play_midi_notes([interval.note1], duration=DURATION)
    clear_event_buffer()
    play_midi_notes([interval.note2], duration=DURATION)


def play_harmonic_interval(interval: Interval):
    clear_event_buffer()
    play_midi_notes([interval.note1, interval.note2], duration=DURATION)


def play_interval() -> GameState:
    global current_interval, state_message, guess_start_time
    current_interval = get_random_interval()
    player = random.choice([play_harmonic_interval, play_melodic_interval])
    player(current_interval)

    state_message = "Guess the interval!"
    guess_start_time = pygame.time.get_ticks()
    return GameState.GUESS


def start_round() -> GameState:
    global MAX_ROUNDS, round_number, state_message
    round_number += 1
    if round_number > MAX_ROUNDS:
        return GameState.GAME_OVER

    state_message = "Playing interval..."
    return GameState.PLAY_INTERVAL


def handle_correct():
    global message, correct
    message = f"Correct! The interval was {
        INTERVAL_NAME[current_interval.interval]}."
    correct += 1


def handle_incorrect(user_interval_guess):
    global message
    message = f"Incorrect! You entered {INTERVAL_NAME[user_interval_guess]}. The correct interval was {
        INTERVAL_NAME[current_interval.interval]}."


def handle_guess() -> GameState:
    global message, correct, state_message, current_interval, guess_start_time, time_elapsed
    time_elapsed = pygame.time.get_ticks() - guess_start_time
    if time_elapsed > TIME_LIMIT:
        message = f"Too slow! The correct interval was {
            INTERVAL_NAME[current_interval.interval]}."
        time_elapsed = TIME_LIMIT  # To ensure display clamps at 0
        return GameState.ROUND_OVER

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            return GameState.EXIT
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                return GameState.EXIT
            user_interval_guess = INPUTS.get(event.key, None)
            if user_interval_guess is not None:
                if user_interval_guess == current_interval.interval:
                    handle_correct()
                else:
                    handle_incorrect(user_interval_guess)
                return GameState.ROUND_OVER

    return GameState.GUESS


def game_over() -> GameState:
    global round_number, message, state_message, correct
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            return GameState.EXIT
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                return GameState.EXIT
            else:
                round_number = 0
                correct = 0
                message = ""
                state_message = ""
                return GameState.ROUND_OVER

    state_message = "Game Over. Press any key to restart or Esc to quit."
    return GameState.GAME_OVER


def get_top_left(surface: pygame.Surface, **kwargs) -> tuple[float, float]:
    rect = surface.get_rect()
    for key, value in kwargs.items():
        setattr(rect, key, value)
    return rect.topleft


def render_font(message: str) -> pygame.Surface:
    return font.render(message, True, (0, 0, 0))


def display_text(message: str, **kwargs):
    display = render_font(message)
    screen.blit(display, get_top_left(display, **kwargs))


# Initialize screen
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption(TITLE)
font = pygame.font.Font(None, FONT_SIZE)

# Game loop
running = True
state = GameState.ROUND_OVER
current_interval: Interval
message = ""
state_message = ""
round_number = 0
correct = 0
guess_start_time = 0
time_elapsed = 0

while running:
    match state:
        case GameState.ROUND_OVER:
            state = start_round()
        case GameState.PLAY_INTERVAL:
            state = play_interval()
        case GameState.GUESS:
            state = handle_guess()
        case GameState.GAME_OVER:
            state = game_over()
        case GameState.EXIT:
            running = False

    # Clear screen
    screen.fill((255, 255, 255))

    # Render image
    screen.blit(keyboard_layout, image_rect.topleft)

    # Render text
    display_text(TITLE, midtop=(SCREEN_WIDTH/2, FONT_SIZE + MARGIN))
    display_text(f"{correct}/{round_number-1}",
                 topright=(SCREEN_WIDTH-MARGIN, FONT_SIZE + MARGIN))
    display_text(f'Time: {((TIME_LIMIT - time_elapsed)/1000):.2f}',
                 center=(SCREEN_WIDTH/2, SCREEN_HEIGHT*2/3 - (FONT_SIZE + MARGIN)))
    display_text(message, center=(SCREEN_WIDTH/2, SCREEN_HEIGHT/3))
    display_text(state_message, center=(SCREEN_WIDTH/2, SCREEN_HEIGHT*2/3))

    # Update display
    pygame.display.flip()

    clock.tick(FPS)

# Quit pygame and midi
pygame.midi.quit()
pygame.quit()
