from poker_game_runner.state import Observation
from poker_game_runner.utils import Range, HandType
import time
import random

class Bot:
   # Initialize the ranges that we will check from
   def __init__(self) -> None:
      self.r51 = Range("22+, A2s+, K2s+, Q3s+, J4s+, T4s+, 94s+, 84s+, 73s+, 63s+, 53s+, 43s, 32s, A2o+, K4o+, Q8o+, J9o+, T9o, 98o")
      self.r45 = Range("22+, A2s+, K2s+, Q4s+, J6s+, T6s+, 95s+, 85s+, 74s+, 63s+, 53s+, 43s, 32s, A2o+, K7o+, Q9o+, J9o+, T9o, 98o")
      self.r30 = Range("22+, A2s+, K6s+, Q8s+, J8s+, T8s+, 97s+, 86s+, 75s+, 65s, 54s, 43s, 32s, A8o+, A5o, KTo+, QTo+, JTo, T9o, 98o")
      self.r22 = Range("22+, A2s+, K8s+, Q9s+, J9s+, T9s, 98s, 87s, 76s, 65s, 54s, ATo+, KTo+, QJo, JTo")
      self.r17 = Range("44+, A2s+, K9s+, Q9s+, J9s+, T9s, 98s, 87s, 76s, ATo+, KJo+")
      self.r12 = Range("77+, A8s+, A4s-A5s, K9s+, Q9s+, J9s+, T9s, 98s, AJo+")
      self.r9 = Range("77+, ATs+, A5s, KTs+, QTs+, J9s+, T9s, 98s, AQo+")
      self.r7 = Range("77+, A9s+, KJs+, AQo+")

   # Bots name
   def get_name(self):
      return "c3310"

   # Final acting, based on if we are in preflop or further
   def act(self, obs: Observation):

      # Collect info on everyones stack to judge how risky we can be
      player_stacks = list()
      for player_info in obs.player_infos:
         player_stacks.append(player_info.stack)
      my_stack = obs.get_my_player_info().stack
      player_stacks.append(my_stack)
      player_stacks.sort()
      my_index = player_stacks.index(my_stack)
      middle_index = len(player_stacks)//2
      my_bias = 0.05 * (my_index - middle_index)

      # If in preflop, run do_preflop, otherwise postflop   
      if obs.current_round == 0:
         return self.do_preflop(my_bias, obs)
      else:
         return self.do_postflop(my_bias, obs)

   # Action to take during preflop   
   def do_preflop(self, my_bias, obs: Observation):
      # do_preflop_open if nobody raised, else preflop_response
      raise_actions = [action for action in obs.get_actions_this_round() if action.action > 1]
      if len(raise_actions) == 0:
         return self.do_preflop_open(my_bias, obs)
      else:
         return self.do_preflop_response(my_bias, obs)
   
   # If hand in r51 range, pot raise by 50%, else call/check
   def do_preflop_open(self, my_bias, obs:Observation):
      open_raise_range = self.r51
      if open_raise_range.is_hand_in_range(obs.my_hand):
         return obs.get_fraction_pot_raise(0.50)
      else:
         return 1

   # Calculate our odds, and play it safer based on it
   def do_preflop_response(self, my_bias, obs:Observation):
      call_odds = obs.get_call_size() / obs.get_pot_size() + my_bias
      if call_odds < 0.1:
         return 1
      elif call_odds < 0.2:
         range_of_cards = self.r30
      elif call_odds < 0.4:
         range_of_cards = self.r22
      elif call_odds < 0.6:
         range_of_cards = self.r17
      elif call_odds < 0.8:
         range_of_cards = self.r12
      elif call_odds < 0.9:
         range_of_cards = self.r9
      else:
         range_of_cards = self.r7

      if range_of_cards.is_hand_in_range(obs.my_hand):
         return 1
      else:
         return 0

   # After first round, we return based on if anyone raised or not
   def do_postflop(self, my_bias, obs:Observation):
      if obs.get_call_size() == 0:
         return self.do_post_flop_open(my_bias, obs)
      else:
         return self.do_post_flop_response(my_bias, obs)

   # If player raised
   def do_post_flop_open(self, my_bias, obs:Observation):
      if self.is_hand_ace_or_better(obs):
         return obs.get_fraction_pot_raise(0.7+my_bias)

   # Check if hand is Ace or Better
   def is_hand_ace_or_better(self, obs:Observation):
      my_hand_type = obs.get_my_hand_type()
      return my_hand_type >= HandType.PAIR or self.is_card_rank_in_hand('A', obs.my_hand)

   # Checks if card ranks in hand
   def is_card_rank_in_hand(self, rank, hand):
      return rank in hand[0] or rank in hand[1]

   # Soemome raised in postflop
   def do_post_flop_response(self, my_bias, obs: Observation):
      call_odds = obs.get_call_size() / obs.get_pot_size() + my_bias
      my_hand_type = obs.get_my_hand_type()
      if call_odds < 0.1:
         return obs.get_fraction_pot_raise(0.1 + my_bias)
      elif call_odds < 0.2:
         if my_hand_type >= HandType.PAIR and my_hand_type.value > obs.get_board_hand_type().value:
            return obs.get_fraction_pot_raise(0.2 + my_bias)
      elif call_odds < 0.5:
         if my_hand_type > HandType.PAIR and my_hand_type.value > obs.get_board_hand_type().value+1:
            return obs.get_fraction_pot_raise(0.2 + my_bias)
      else:
         if my_hand_type > HandType.TWOPAIR and my_hand_type.value > obs.get_board_hand_type().value+1:
            return obs.get_fraction_pot_raise(0.2 + my_bias)

      return 0

   