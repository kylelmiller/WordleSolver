"""Helps solve unknown Wordle puzzles and gives statistical information on choices."""
import random

from gamestate import GameState

random.seed(1174321)


def main() -> None:
    """
    Helps solve unknown Wordle puzzles and gives statistical information on choices.

    :return:
    """

    with open("dictionary.txt", "r", encoding="utf-8") as fi:
        words = [w.strip().lower() for w in fi.readlines()]

    while True:
        game_state = GameState(words)

        print("You need to add the output result of each round. Example of output is:")
        print("r0t2a means 'r' in the first spot, 't' in the 3rd spot and 'a' is in the result.")

        while not game_state.is_game_over():
            best_choices = game_state.get_monte_carlo_choices()
            print("Suggested choices:")
            for choice in best_choices:
                print(f"{choice[1]} ({choice[0]})")
            word_choice = input("What is your word choice?")
            while len(word_choice) != game_state.HIDDEN_WORD_LENGTH:
                word_choice = input(
                    f"The word you entered is not the correct length of {game_state.HIDDEN_WORD_LENGTH}. "
                    "What is your word choice?"
                )
            if word_choice not in {choice[1] for choice in best_choices}:
                print(
                    f"That choice changes the projected win percentage to {game_state.get_percentage_chance_of_winning(word_choice)}"
                )
            outcome = input("What was the outcome?")
            print("Calculating")
            game_state.update_with_text_outcome(word_choice, outcome)


if __name__ == "__main__":
    main()
