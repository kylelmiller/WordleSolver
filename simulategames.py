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
    game_won = []
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
                game_won.append(True)
                break
        else:
            game_won.append(False)
            misses.add(hidden_word)
            print(f"Failed to guess '{hidden_word}'")

        for word in game_state.previous_tries:
            choice_outcomes[word].append(game_won[-1])

        if i % 100 == 0:
            print(sum(game_won) / len(game_won))
    print(sum(game_won) / len(game_won))
    print(
        [
            (k, sum(choice_outcomes[k]) / len(choice_outcomes[k]))
            for k in choice_outcomes
            if len(choice_outcomes[k]) > times_to_play / 25
        ]
    )
    print(f"The misses were: {misses}")


if __name__ == "__main__":
    main()
