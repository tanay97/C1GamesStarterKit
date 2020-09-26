import gamelib
import random
import math
import warnings
from sys import maxsize
import json


"""
Most of the algo code you write will be in this file unless you create new
modules yourself. Start by modifying the 'on_turn' function.

Advanced strategy tips: 

  - You can analyze action frames by modifying on_action_frame function

  - The GameState.map object can be manually manipulated to create hypothetical 
  board states. Though, we recommended making a copy of the map to preserve 
  the actual current map state.
"""

class AlgoStrategy(gamelib.AlgoCore):
    def __init__(self):
        super().__init__()
        seed = random.randrange(maxsize)
        random.seed(seed)
        gamelib.debug_write('Random seed: {}'.format(seed))

    def on_game_start(self, config):
        """ 
        Read in config and perform any initial setup here 
        """
        gamelib.debug_write('Configuring your custom algo strategy...')
        self.config = config
        global FILTER, ENCRYPTOR, DESTRUCTOR, PING, EMP, SCRAMBLER, BITS, CORES
        FILTER = config["unitInformation"][0]["shorthand"]
        ENCRYPTOR = config["unitInformation"][1]["shorthand"]
        DESTRUCTOR = config["unitInformation"][2]["shorthand"]
        PING = config["unitInformation"][3]["shorthand"]
        EMP = config["unitInformation"][4]["shorthand"]
        SCRAMBLER = config["unitInformation"][5]["shorthand"]
        BITS = 1
        CORES = 0
        # This is a good place to do initial setup
        self.DEFAULT_SPAWN = [5, 8]
        self.scored_on_locations = []
        self.damaged_enemy_locations = []
        self.damaged_enemy = False
        self.defense_strat = 1
        self.wall_state = 0
    

    def on_turn(self, turn_state):
        """
        This function is called every turn with the game state wrapper as
        an argument. The wrapper stores the state of the arena and has methods
        for querying its state, allocating your current resources as planned
        unit deployments, and transmitting your intended deployments to the
        game engine.
        """
        game_state = gamelib.GameState(self.config, turn_state)
        gamelib.debug_write('Performing turn {} of your custom algo strategy'.format(game_state.turn_number))
        game_state.suppress_warnings(True)  #Comment or remove this line to enable warnings.

        # self.starter_strategy(game_state)
        self.reactive_scramblers(game_state)
        
        if game_state.turn_number < 8:
            [wall_cheese, side] = self.detect_wall_cheese(game_state)
            if wall_cheese:
                self.update_defense(game_state, side)
        self.build_defences(game_state)
        self.attack_strategy(game_state)

        gamelib.debug_write('Wall cheese detected: {}'.format(self.detect_wall_cheese(game_state)))

        self.scored_on_locations = []

        game_state.submit_turn()


    """
    NOTE: All the methods after this point are part of the sample starter-algo
    strategy and can safely be replaced for your custom algo.
    """
    def attack_strategy(self, game_state):
        #possible_spawns = [[12, 1], [11, 2], [15, 1], [16, 2]]
        #possible_spawns = [[6,7],[21,7]]
        #possible_spawns = [[6,7]]
        if self.wall_state == 0:
            possible_spawns = [[4,9]]
        elif self.wall_state == 1:
            possible_spawns = [[5,8]]
        b_t = self.least_damage_spawn_location(game_state, possible_spawns)
        best_location = b_t[0]
        damage_taken = b_t[1]
        #SEND SCRAMBLES IF ENCRYPTORS DOWN
        gamelib.debug_write('Bits gotten: {}'.format(game_state.BITS))
        gamelib.debug_write('best locations is {}'.format(best_location))

        num_emps = int(game_state.turn_number / 8) + 2

        if game_state.turn_number == 3:
            game_state.attempt_spawn(EMP, best_location, 4)
        elif game_state.turn_number >= 3:
            if False and self.damaged_enemy:
                if game_state.get_resource(BITS) >= 6:
                    game_state.attempt_spawn(PING, best_location, 6)
                    self.damaged_enemy = False
                else:
                    game_state.attempt_spawn(SCRAMBLER, best_location, 1)
            else:
                if self.damaged_enemy:
                    game_state.attempt_spawn(EMP, best_location, 2)
                elif game_state.get_resource(BITS) >= num_emps * 3:
                    game_state.attempt_spawn(EMP, best_location, num_emps)
                    self.damaged_enemy = False
                else:
                    pass
                    #game_state.attempt_spawn(SCRAMBLER, best_location, 1)
        self.damaged_enemy = False


    def update_defense(self, game_state, side):
        #if side == "l":
            i = 3
        #else:
        #    #change opening
        #    pass

    def detect_wall_cheese(self, game_state):
        rows_to_check = []
        start = 0
        finish = 28
        y = 14
        while y < 17:
            temp = []
            for x in range(start, finish):
                temp.append([x, y])
            rows_to_check.append(temp)
            finish -= 1
            start +=1
            y+=1
        
        wall_cheese = False
        side = ""

        for row in rows_to_check:
            num_defence = 0
            #check from left to right
            wall_length_from_left = 0
            for pos in row:
                if game_state.contains_stationary_unit(pos):
                    wall_length_from_left += 1
                else:
                    #wall ended
                    break
            #check from right to left
            wall_length_from_right = 0
            for pos in reversed(row):
                if game_state.contains_stationary_unit(pos):
                    wall_length_from_right += 1
                else:
                    break
            #wall length on any side is 70% of the row
            if wall_length_from_right > 0.6 * len(row):
                side = "l"
            elif wall_length_from_left > 0.6 * len(row):             
                side = "r"

            if side != "":
                wall_cheese = True
                self.wall_state = 1
                base_encryptor_locations = [[5,9],[5,10],[5,11],[6,11]]
                game_state.attempt_remove(base_encryptor_locations)

                break
        return [wall_cheese, side]

    def check_for_block(game_state):

        target_location = game_state.find_path_to_edge([self.DEFAULT_SPAWN], game_state.get_target_edge(self.DEFAULT_SPAWN))



    # def starter_strategy(self, game_state):
    #     game_state.attempt_spawn(EMP, [24, 10], 3)
    #     """
    #     For defense we will use a spread out layout and some Scramblers early on.
    #     We will place destructors near locations the opponent managed to score on.
    #     For offense we will use long range EMPs if they place stationary units near the enemy's front.
    #     If there are no stationary units to attack in the front, we will send Pings to try and score quickly.
    #     """
    #     # First, place basic defenses
    #     self.build_defences(game_state)
    #     # Now build reactive defenses based on where the enemy scored
    #     self.build_reactive_defense(game_state)

    #     # If the turn is less than 5, stall with Scramblers and wait to see enemy's base
    #     if game_state.turn_number < 5:
    #         self.stall_with_scramblers(game_state)
    #     else:
    #         # Now let's analyze the enemy base to see where their defenses are concentrated.
    #         # If they have many units in the front we can build a line for our EMPs to attack them at long range.
    #         if self.detect_enemy_unit(game_state, unit_type=None, valid_x=None, valid_y=[14, 15]) > 10:
    #             self.emp_line_strategy(game_state)
    #         else:
    #             # They don't have many units in the front so lets figure out their least defended area and send Pings there.

    #             # Only spawn Ping's every other turn
    #             # Sending more at once is better since attacks can only hit a single ping at a time
    #             if game_state.turn_number % 2 == 1:
    #                 # To simplify we will just check sending them from back left and right
    #                 ping_spawn_location_options = [[13, 0], [14, 0]]
    #                 best_location = self.least_damage_spawn_location(game_state, ping_spawn_location_options)
    #                 game_state.attempt_spawn(PING, best_location, 1000)

    #             # Lastly, if we have spare cores, let's build some Encryptors to boost our Pings' health.
    #             encryptor_locations = [[13, 2], [14, 2], [13, 3], [14, 3]]
    #             game_state.attempt_spawn(ENCRYPTOR, encryptor_locations)

    def build_defences(self, game_state):
        """
        Build basic defenses using hardcoded locations.
        Remember to defend corners and avoid placing units in the front where enemy EMPs can attack them.
        """
        # Useful tool for setting up your base locations: https://www.kevinbai.design/terminal-map-maker
        # More community tools available at: https://terminal.c1games.com/rules#Download

        # Place destructors that attack enemy units
        if self.wall_state == 0:
            base_destructor_locations = [[3,13],[7,13],[11,13],[16,13],[20,13],[24,13]]
            base_filter_locations = [[0,13],[1,13],[2,13],[4,13],[5,13],[6,13],[8,13],[9,13],[10,13],[12,13],[13,13],[14,13],[15,13],[17,13],[18,13],[19,13],[21,13],[22,13],[23,13],[25,13],[27,13]]

            base_encryptor_locations = [[5,9],[5,10],[5,11],[6,11]]

            upgrades = [[27,13],[25,13],[24,13]]
            
            secondary_right_destructor_locations = [[25,11],[24,11],[22,11]]
            secondary_left_desctructor_locations = [[19,11],[15,11],[12,11],[9,11],[6,10],[3,11]]
        elif self.wall_state == 1:
            base_destructor_locations = [[0,13],[3,12],[7,12],[11,12],[16,12],[20,12],[24,12],[27,13]]
            base_filter_locations = [[1,12],[2,12],[4,12],[5,12],[6,12],[8,12],[8,12],[9,12],[10,12],[12,12],[13,12],[14,12],[15,12],[17,12],[18,12],[19,12],[21,12],[22,12],[23,12],[26,12]]

            base_encryptor_locations = [[6,8],[6,9],[6,10],[7,10]]

            upgrades = [[27,13],[0,13],[24,12],[3,12]]

            secondary_right_destructor_locations = [[25,10],[24,10],[22,10]]
            secondary_left_desctructor_locations = [[19,10],[15,10],[12,10],[9,10],[7,9],[3,10]]
        
        if self.defense_strat == 0:
            base_destructor_locations = [[3,13],[7,13],[11,13],[16,13],[20,13],[24,13]]
        elif self.defense_strat == 1:

            if game_state.turn_number == 0:
                game_state.attempt_spawn(DESTRUCTOR, base_destructor_locations)
            else:
                game_state.attempt_spawn(DESTRUCTOR, base_destructor_locations)
                successful_base_spawn = True
                for location in base_destructor_locations:
                    if game_state.can_spawn(FILTER, location, 1):
                        successful_base_spawn = False
                if successful_base_spawn: 
                    game_state.attempt_spawn(FILTER, base_filter_locations)
                    game_state.attempt_spawn(ENCRYPTOR, base_encryptor_locations)
                    game_state.attempt_upgrade(upgrades)
                    game_state.attempt_spawn(DESTRUCTOR, secondary_right_destructor_locations)
                    game_state.attempt_spawn(DESTRUCTOR, secondary_left_desctructor_locations)

        else:
            base_destructor_locations = [[10,12],[17,12],[8,10],[19,10]]
            base_filter_locations = [[0,13],[1,12],[2,11],[3,10],[4,9],[8,11],[9,12],[10,13],[17,13],[18,12],[19,11],[27,13],[26,12],[25,11],[24,10],[23,9]]

            next_filter_locations = [[5,8],[6,8],[7,8],[22,8],[21,8],[20,8],[13,11],[14,11]]
            next_destructor_locations = [[13,10],[14,10]]

            base_encryptor_locations = [[13,2],[14,2]]
            next_encryptor_locations = [[13,3],[14,3]]
            
            game_state.attempt_spawn(DESTRUCTOR, base_destructor_locations)
            game_state.attempt_spawn(FILTER, base_filter_locations)

            game_state.attempt_spawn(FILTER, next_filter_locations)

            game_state.attempt_spawn(ENCRYPTOR, base_encryptor_locations)

            game_state.attempt_spawn(DESTRUCTOR, next_destructor_locations)

            game_state.attempt_spawn(ENCRYPTOR, next_encryptor_locations)

            game_state.attempt_upgrade(base_destructor_locations)

    def build_reactive_defense(self, game_state):
        """
        This function builds reactive defenses based on where the enemy scored on us from.
        We can track where the opponent scored by looking at events in action frames 
        as shown in the on_action_frame function
        """



        # for location in self.scored_on_locations:
        #     # Build destructor one space above so that it doesn't block our own edge spawn locations
        #     build_location = [location[0], location[1]+1]
        #     game_state.attempt_spawn(DESTRUCTOR, build_location)

    def reactive_scramblers(self, game_state):

        """
        Send out Scramblers at random locations to defend our base from enemy moving units.
        """
        if self.scored_on_locations != []:
            possible_spawns = self.scored_on_locations
            #get first location we got scored on and get target edge 
            target_edge = game_state.get_target_edge(self.scored_on_locations[0])
            if target_edge == game_state.game_map.TOP_RIGHT:
                spawn_edge = game_state.game_map.BOTTOM_LEFT
                possible_spawns = [[1, 12], [2, 11], [3, 10], [4, 9]] 
            else:
                spawn_edge = game_state.game_map.BOTTOM_RIGHT
                possible_spawns = [[26, 12], [25, 11], [24, 10], [23, 9]]

            gamelib.debug_write("Spawn locations: {}".format(possible_spawns))
            best_spawn = self.least_damage_spawn_location(game_state, possible_spawns)[0]

            if game_state.get_resource(BITS) >= 5:
                bits_next_turn = game_state.project_future_bits(1, 1)
                if bits_next_turn >= 10:
                    if game_state.can_spawn(SCRAMBLER, best_spawn):
                        game_state.attempt_spawn(SCRAMBLER, best_spawn, 2)
                elif bits_next_turn >= 6:
                    if game_state.can_spawn(SCRAMBLER, best_spawn):
                        game_state.attempt_spawn(SCRAMBLER, best_spawn, 1)


    def emp_line_strategy(self, game_state):
        """
        Build a line of the cheapest stationary unit so our EMP's can attack from long range.
        """
        # First let's figure out the cheapest unit
        # We could just check the game rules, but this demonstrates how to use the GameUnit class
        stationary_units = [FILTER, DESTRUCTOR, ENCRYPTOR]
        cheapest_unit = FILTER
        for unit in stationary_units:
            unit_class = gamelib.GameUnit(unit, game_state.config)
            if unit_class.cost[game_state.BITS] < gamelib.GameUnit(cheapest_unit, game_state.config).cost[game_state.BITS]:
                cheapest_unit = unit

        # Now let's build out a line of stationary units. This will prevent our EMPs from running into the enemy base.
        # Instead they will stay at the perfect distance to attack the front two rows of the enemy base.
        for x in range(27, 5, -1):
            game_state.attempt_spawn(cheapest_unit, [x, 11])

        # Now spawn EMPs next to the line
        # By asking attempt_spawn to spawn 1000 units, it will essentially spawn as many as we have resources for
        game_state.attempt_spawn(EMP, [24, 10], 1000)

    def least_damage_spawn_location(self, game_state, location_options):
        """
        This function will help us guess which location is the safest to spawn moving units from.
        It gets the path the unit will take then checks locations on that path to 
        estimate the path's damage risk.
        """
        damages = []
        # Get the damage estimate each path will take
        for location in location_options:
            path = game_state.find_path_to_edge(location)
            damage = 0
            if path == []:
                gamelib.debug_write("skipped location {}".format(location))
                continue
            for path_location in path:
                # Get number of enemy destructors that can attack the final location and multiply by destructor damage
                damage += len(game_state.get_attackers(path_location, 0)) * gamelib.GameUnit(DESTRUCTOR, game_state.config).damage_i
            damages.append(damage)
        
        # Now just return the location that takes the least damage
        return [location_options[damages.index(min(damages))], min(damages)]

    def find_longest_path(self, game_state, location_options):
        longest_length = 0
        best_location = [0, 0]
        for location in location_options:
            path = game_state.find_path_to_edge(location)
            length = len(path)
            if length > longest_length:
                longest_length = length
                best_location = location
        return best_location
        

    def detect_enemy_unit(self, game_state, unit_type=None, valid_x = None, valid_y = None):
        total_units = 0
        for location in game_state.game_map:
            if game_state.contains_stationary_unit(location):
                for unit in game_state.game_map[location]:
                    if unit.player_index == 1 and (unit_type is None or unit.unit_type == unit_type) and (valid_x is None or location[0] in valid_x) and (valid_y is None or location[1] in valid_y):
                        total_units += 1
        return total_units
        
    def filter_blocked_locations(self, locations, game_state):
        filtered = []
        for location in locations:
            if not game_state.contains_stationary_unit(location):
                filtered.append(location)
        return filtered

    def on_action_frame(self, turn_string):
        """
        This is the action frame of the game. This function could be called 
        hundreds of times per turn and could slow the algo down so avoid putting slow code here.
        Processing the action frames is complicated so we only suggest it if you have time and experience.
        Full doc on format of a game frame at: https://docs.c1games.com/json-docs.html
        """
        # Let's record at what position we get scored on
        state = json.loads(turn_string)
        events = state["events"]
        breaches = events["breach"]
        for breach in breaches:
            location = breach[0]
            unit_owner_self = True if breach[4] == 1 else False
            # When parsing the frame data directly, 
            # 1 is integer for yourself, 2 is opponent (StarterKit code uses 0, 1 as player_index instead)
            if not unit_owner_self:
                gamelib.debug_write("Got scored on at: {}".format(location))
                self.scored_on_locations.append(location)
                gamelib.debug_write("All locations: {}".format(self.scored_on_locations))
            else:
                gamelib.debug_write("Scored on the enemy at: {}".format(location))
                self.damaged_enemy_locations.append(location)
                self.damaged_enemy = True
            


if __name__ == "__main__":
    algo = AlgoStrategy()
    algo.start()
