"""Simulates many potential Wordle puzzles and solves them using Monte Carlo"""
import random
from collections import defaultdict

from gamestate import GameState

random.seed(1174321)


def main(times_to_play=5000) -> None:
    """
    Simulates many potential Wordle puzzles and solves them using Monte Carlo

    :param times_to_play: Number of simulated games to run
    :return: None
    """

    with open("dictionary.txt", "r", encoding="utf-8") as fi:
        words = [w.strip().lower() for w in fi.readlines()]

    choice_outcomes = defaultdict(list)
    turns_to_win = []
    misses = set()
    for i in range(times_to_play):
        hidden_word = random.choice(words)
        print(f"Hidden word is: {hidden_word}")
        game_state = GameState(words, verbose=True)
        while not game_state.is_game_over():
            best_guess = game_state.get_monte_carlo_choice()
            game_state.update_with_hidden_word(best_guess, hidden_word)
            if best_guess == hidden_word:
                print("Guessed correctly!")
                turns_to_win.append(len(game_state.previous_tries))
                break
        else:
            turns_to_win.append(None)
            misses.add(hidden_word)
            print(f"Failed to guess '{hidden_word}'")

        for word in game_state.previous_tries:
            choice_outcomes[word].append(turns_to_win[-1])

        if i % 100 == 0:
            exclude_losses = [v for v in turns_to_win if v is not None]
            print(f"Losses: {len(turns_to_win) - len(exclude_losses)}")
            print(sum(exclude_losses) / len(exclude_losses))

    exclude_losses = [v for v in turns_to_win if v is not None]
    print(f"Losses: {len(turns_to_win) - len(exclude_losses)}")
    print(sum(exclude_losses) / len(exclude_losses))
    print(
        [
            (k, sum(choice_outcomes[k]) / len(choice_outcomes[k]))
            for k in choice_outcomes
            if len(choice_outcomes[k]) >= times_to_play / 50
        ]
    )
    print(f"The misses were: {misses}")


if __name__ == "__main__":
    main(times_to_play=200_000)
