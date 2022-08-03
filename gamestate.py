"""Class for keeping track of Wordle game state and providing choices"""
import heapq
import math
import random
import re
from collections import Counter, defaultdict
from copy import deepcopy
from typing import List


class GameState:
    """
    Class for keeping track of Wordle game state and providing choices
    """

    MAX_MONTE_CARLO_SIMILATED_OUTCOMES = 50_000
    TOTAL_GUESSES = 6
    HIDDEN_WORD_LENGTH = 5
    MAX_CONSIDERED_GOOD_GUESSES = 50
    GAME_LOST_PENALTY_MULTIPLIER = 10
    LETTER_KNOWN_PENALTY = 0.01

    def __init__(self, dictionary: List[str], **kwargs):
        self.dictionary = dictionary
        self.remaining_words = kwargs.get("remaining_words", dictionary)
        self.total_guesses = kwargs.get("total_guesses", self.TOTAL_GUESSES)
        self.verbose = kwargs.get("verbose", False)
        self.excluded_letters = kwargs.get("excluded_letters", set())
        self.included_letters = kwargs.get("included_letters", set())
        self.included_letter_positions = kwargs.get("included_letter_positions", {})
        self.included_letter_not_positions = kwargs.get("included_letter_not_positions", defaultdict(set))
        self.previous_tries = []

    def __matches_letter_positions(self, word: str) -> bool:
        """
        Takes a word and checks to see if the letters in the word matches the letter positions of the hidden word.

        :param word: The word we are checking
        :return: True if the word has the correct letters in the correct positions, else False
        """
        characters_not_matched = list(self.included_letter_positions)
        for i, v in enumerate(word):
            if self.included_letter_positions.get(v, None) == i:
                characters_not_matched.remove(v)
        return len(characters_not_matched) == 0

    def __get_new_remaining_words(self, guessed_word: str) -> List[str]:
        """
        Given the guessed word, remove all words that can no longer be the hidden word.

        :param guessed_word: The word that was guessed
        :return: The list of updated potential hidden words
        """
        return [
            word
            for word in self.remaining_words
            if not (set(word) & self.excluded_letters)
            and len(set(word) & self.included_letters) == len(self.included_letters)
            and self.__matches_letter_positions(word)
            # if we know an included character is not in a location remove those words
            and not any(i in self.included_letter_not_positions[c] for i, c in enumerate(word)) and word != guessed_word
        ]

    def is_game_over(self) -> bool:
        """
        Checks to see if the game is over.

        :return: True if the game is over, else False
        """
        return (
            len(self.previous_tries) >= self.total_guesses
            or len(self.included_letter_positions) == self.HIDDEN_WORD_LENGTH
        )

    def update_with_text_outcome(self, guessed_word: str, outcome: str) -> None:
        """
        Updates the game state given the guessed word and the outcome of that guess.
        The outcome is a string of a special format. The format is letters for letters that matched and letters followed
        by a number of the index if the letter matched a position. The index starts from 0 and goes to a maximum of 4.

        Some examples of valid outcome strings would be:
        stba
        s0t4b1a
        st4ba

        :param guessed_word: The word that was guessed
        :param outcome:  The outcome of that guess
        :return: None
        """
        self.previous_tries.append(guessed_word)

        self.included_letters |= set(re.sub(r"\d", "", outcome))
        self.excluded_letters |= {c for c in guessed_word if c not in self.included_letters}

        position_values = ["" for _ in range(self.HIDDEN_WORD_LENGTH)]
        for i, character in enumerate(outcome):
            if character.isnumeric():
                position_values[int(character)] = outcome[i - 1]

        for i, c in enumerate(guessed_word):
            if c == position_values[i]:
                self.included_letter_positions[c] = i
            elif c in self.included_letters:
                self.included_letter_not_positions[c].add(i)

        self.remaining_words = self.__get_new_remaining_words(guessed_word)

    def update_with_hidden_word(self, guessed_word: str, hidden_word: str) -> None:
        """
        Updates the game state given the guessed word and the known hidden word.

        :param guessed_word: The word that was guessed
        :param hidden_word: The hidden word you are trying to find
        :return: None
        """
        if self.verbose:
            print(f"Guessing {guessed_word}")

        self.previous_tries.append(guessed_word)

        self.included_letters |= set(guessed_word) & set(hidden_word)
        self.excluded_letters |= {c for c in guessed_word if c not in hidden_word}

        for i, c in enumerate(guessed_word):
            if c == hidden_word[i]:
                self.included_letter_positions[c] = i
            elif c in self.included_letters:
                self.included_letter_not_positions[c].add(i)

        self.remaining_words = self.__get_new_remaining_words(guessed_word)

    def get_best_guess(self) -> str:
        """
        Gets the best guess given the algorithm.
        The algorithm takes the letters remaining in all the words that could potentially be the hidden word. It
        counts all the letters and then creates a weighted score for all letters based on letters remaining and
        the amount of information gain for each letter. It then takes the top X words in the entire dictionary based
        on the letter scoring and randomly selects one of them as the best guess.

        :return:
        """
        if len(self.remaining_words) <= 2:
            return random.choice(self.remaining_words)

        character_counter = Counter("".join(self.remaining_words))

        for c in self.included_letters:

            if c in self.included_letter_positions:
                # We gain no new information from included letters with positions
                character_counter[c] = 0
            else:
                # We gain some information from included letters with no positions
                character_counter[c] *= self.LETTER_KNOWN_PENALTY

        max_occurance = max(character_counter.values())
        character_scores = {c: v / max(1, max_occurance) for c, v in character_counter.items()}

        word_scores_heap = []
        for word in (
            self.dictionary
            if (
                (len(character_counter) != len(self.included_letters))
                and (self.total_guesses > len(self.previous_tries) + 1)
                and len(self.remaining_words) > 2
            )
            else self.remaining_words
        ):
            score = sum(character_scores.get(c, 0) for c in set(word))
            if len(word_scores_heap) < max(
                min(math.ceil(len(self.remaining_words) / 5), self.MAX_CONSIDERED_GOOD_GUESSES), 5
            ):
                heapq.heappush(word_scores_heap, (score, word))
            elif score > word_scores_heap[0][0]:
                heapq.heapreplace(word_scores_heap, (score, word))

        solution_words = [v[1] for v in word_scores_heap]
        if len(self.remaining_words) <= 5:
            solution_words = list(set(solution_words) | set(self.remaining_words))

        return random.choice(solution_words)

    def deepcopy(self):  # -> GameState
        """
        Returns a deep copy of the game state for certain member variables.

        :return: Deep copy of a portion of the GameState
        """
        return GameState(
            self.dictionary,
            remaining_words=list(self.remaining_words),
            total_guesses=self.total_guesses - len(self.previous_tries),
            excluded_letters=set(self.excluded_letters),
            included_letters=set(self.included_letters),
            included_letter_positions=dict(self.included_letter_positions),
            included_letter_not_positions=deepcopy(self.included_letter_not_positions),
        )

    def get_percentage_chance_of_winning(self, guess_word, number_of_simulations=2000):
        """
        If the given guess word used next, what is the percentage chance of winning the game. This is calculated using
        X number of game simulations with randomly selected hidden words from the remaining hidden words.

        :param guess_word: The guess word
        :param number_of_simulations: The number of times we want to simulate the outcome
        :return: The win rate percentage
        """
        outcomes = []
        for _ in range(number_of_simulations):
            hidden_word = random.choice(self.remaining_words)
            if guess_word == hidden_word:
                outcomes.append(True)
                continue

            monte_carlo_game_state = self.deepcopy()

            monte_carlo_game_state.update_with_hidden_word(guess_word, hidden_word)
            while not monte_carlo_game_state.is_game_over():
                best_guess = monte_carlo_game_state.get_best_guess()
                monte_carlo_game_state.update_with_hidden_word(best_guess, hidden_word)
                if best_guess == hidden_word:
                    outcomes.append(True)
                    break
            else:
                outcomes.append(False)
        return sum(outcomes) / len(outcomes)

    def get_monte_carlo_choices(self, limit=5):
        """
        Gets the top X word choices for the current game state. This is calculated using Monte Carlo.

        :param limit: The number of choices to return
        :return: The list of word choices with the percentage chance of a win.
        """

        if len(self.previous_tries) == 0:
            return [
                (3.959705882352941, "dates"),
                (3.970299884659746, "dales"),
                (3.971229293809939, "dares"),
                (3.984014209591474, "lanes"),
                (3.988081725312145, "rates"),
            ]

        number_of_simulations = min(len(self.remaining_words) * 50, self.MAX_MONTE_CARLO_SIMILATED_OUTCOMES)
        choice_outcomes = defaultdict(list)
        for _ in range(number_of_simulations):
            hidden_word = random.choice(self.remaining_words)
            monte_carlo_game_state = self.deepcopy()
            while not monte_carlo_game_state.is_game_over():
                best_guess = monte_carlo_game_state.get_best_guess()
                monte_carlo_game_state.update_with_hidden_word(best_guess, hidden_word)
                if best_guess == hidden_word:
                    choice_outcomes[monte_carlo_game_state.previous_tries[0]].append(
                        len(monte_carlo_game_state.previous_tries + self.previous_tries)
                    )
                    break
            else:
                choice_outcomes[monte_carlo_game_state.previous_tries[0]].append(
                    len(monte_carlo_game_state.previous_tries + self.previous_tries) * self.GAME_LOST_PENALTY_MULTIPLIER
                )

        return sorted([(sum(outcomes) / float(len(outcomes)), word) for word, outcomes in choice_outcomes.items()])[
            :limit
        ]

    def get_monte_carlo_choice(self):
        """
        Gets the top monte carlo word choice given the current game state.

        :return: Word with the top win rate given the current game state
        """
        return self.get_monte_carlo_choices(limit=1)[0][1]
