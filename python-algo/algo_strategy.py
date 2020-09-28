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
        global WALL, FACTORY, TURRET, SCOUT, DEMOLISHER, INTERCEPTOR, MP, SP
        WALL = config["unitInformation"][0]["shorthand"]
        FACTORY = config["unitInformation"][1]["shorthand"]
        TURRET = config["unitInformation"][2]["shorthand"]
        SCOUT = config["unitInformation"][3]["shorthand"]
        DEMOLISHER = config["unitInformation"][4]["shorthand"]
        INTERCEPTOR = config["unitInformation"][5]["shorthand"]
        MP = 1
        SP = 0
        # This is a good place to do initial setup
        self.scored_on_locations = {}
        self.enemy_unit_movement = []
        self.frame_count = 0

        self.recurring_line_crossing = {}

        self.build_queue = []
        self.upgrade_queue = []
        self.initialize_queues()

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

        for instance in self.enemy_unit_movement:
            if (instance[0], instance[1][0][0]) not in self.recurring_line_crossing:
                self.recurring_line_crossing[(instance[0], instance[1][0][0])] = 1
            else:
                self.recurring_line_crossing[(instance[0], instance[1][0][0])] += 1

        self.recurring_line_crossing = {k: v for k, v in sorted(self.recurring_line_crossing.items(), key=lambda item: item[1])}

        gamelib.debug_write(self.recurring_line_crossing)

        game_state.suppress_warnings(True)  #Comment or remove this line to enable warnings.

        self.starter_strategy(game_state)

        game_state.submit_turn()

        self.frame_count = 0
        self.enemy_unit_movement = []
        self.scored_on_locations = {}


    """
    NOTE: All the methods after this point are part of the sample starter-algo
    strategy and can safely be replaced for your custom algo.
    """
    def initialize_queues(self):
        self.factory_base_locations = { "type": FACTORY, 
                                        "loc": [[11, 7], [12, 7], [13, 7]]
                                        }
        self.factory_extra_locations = { "type": FACTORY,
                                        "loc": [[14, 7], [15, 7], [16, 7], [12, 6], [13, 6], [14, 6], [15, 6], 
                                        [13, 5], [14, 5], [9, 7], [10, 7],
                                        [17, 7], [18, 7], [10, 6], [11, 6], [16, 6], [17, 6], [11, 5], [12, 5], 
                                        [15, 5], [16, 5], [12, 4], [13, 4], [14, 4], [15, 4], [13, 3], [14, 3]]
                                         }
        # V-shape wall setup
        self.wall_left_location = { "type": WALL,
                                    "loc": [[0,13], [1, 13], [2, 13], [3, 13]]
                                    }
        self.wall_right_location = { "type": WALL,
                                    "loc": [[24,13], [25, 13], [26, 13], [27, 13]]
                                    }
        self.wall_base_location = { "type": WALL,
                                   "loc": [[4, 12], [23, 12], [5, 11], [22, 11], [6, 10], [21, 10], [7, 9], 
                                   [20, 9], [8, 8], [9, 8], [10, 8], [11, 8], [12, 8], [13, 8], [14, 8], 
                                   [15, 8], [16, 8], [17, 8], [18, 8], [19, 8]]
                                   }
        # V-shape turrent setup
        self.turret_base_locations = { "type": TURRET,
                                    "loc": [[3, 12], [24, 12]]
                                    }
        self.turret_right_locations = { "type": TURRET,
                                    "loc": [[24, 12], [23, 11], [22, 12], [22, 10]]
                                    }
        self.turret_left_locations = { "type": TURRET,
                                    "loc": [[3, 12], [4, 11], [5, 12], [5, 10]]
                                    }
        self.base_build = [self.factory_base_locations]
        self.build_queue = []

    def starter_strategy(self, game_state):
        """
        For defense we will use a spread out layout and some interceptors early on.
        We will place turrets near locations the opponent managed to score on.
        For offense we will use long range demolishers if they place stationary units near the enemy's front.
        If there are no stationary units to attack in the front, we will send Scouts to try and score quickly.
        """

        self.build_defences(game_state)
        self.attack_strategy(game_state)

            # self.scout_attack(game_state, int(0.5*game_state.get_resource(MP)))
    
    def attack_strategy(self, game_state):
        if game_state.turn_number < 10:
            interceptor_ratio = 1
            demolisher_ratio = 0
            scout_ratio = 0
        else:
            interceptor_ratio = 0.3
            # demolisher_ratio = 0.7
            scout_ratio = 0.7
        if game_state.turn_number < 3:
            game_state.attempt_spawn(INTERCEPTOR, [7, 6], int(game_state.number_affordable(INTERCEPTOR)*interceptor_ratio/2))
            game_state.attempt_spawn(INTERCEPTOR, [20, 6], int(game_state.number_affordable(INTERCEPTOR)*interceptor_ratio/2))
        else:
            self.stall_with_interceptors(game_state, int(interceptor_ratio*game_state.get_resource(MP)))
            # self.demolisher_attack(game_state, int(demolisher_ratio*game_state.number_affordable(DEMOLISHER)))
            self.scout_attack(game_state, int(scout_ratio*game_state.number_affordable(SCOUT)))
        if game_state.turn_number > 20:
            game_state.attempt_spawn(DEMOLISHER, [16, 2], game_state.number_affordable(DEMOLISHER))

    def build_defences(self, game_state):
        """
        Build basic defenses using hardcoded locations.
        Remember to defend corners and avoid placing units in the front where enemy demolishers can attack them.
        """
        # Useful tool for setting up your base locations: https://www.kevinbai.design/terminal-map-maker
        # More community tools available at: https://terminal.c1games.com/rules#Download
        if game_state.turn_number == 0:
            game_state.attempt_spawn(FACTORY, self.factory_base_locations["loc"])
            game_state.attempt_upgrade(self.factory_base_locations["loc"])
            return
        if game_state.turn_number == 1:
            self.base_build = [self.turret_base_locations, self.factory_base_locations]
        if game_state.turn_number == 2:
            self.base_build = [self.wall_base_location, self.wall_left_location, self.factory_base_locations]
        if game_state.turn_number == 5:
            self.base_build = [self.wall_left_location, self.wall_base_location, self.turret_base_locations, self.factory_base_locations]
            self.build_queue.append(self.factory_extra_locations)
        if game_state.turn_number == 15:
            self.base_build.append(self.turret_right_locations)

        for struct in self.base_build:
            game_state.attempt_spawn(struct["type"], struct["loc"])

        if self.scored_on_locations and game_state.turn_number > 10:
            damage_location = max(self.scored_on_locations, key=self.scored_on_locations.get)
            damage_side = "left" if damage_location[0] < 13 else "right"
            if damage_location[0] < 13:
                self.build_queue.clear()
                self.build_queue.append(self.turret_left_locations)
                self.build_queue.append(self.factory_extra_locations)
            else:
                self.build_queue.clear()
                self.build_queue.append(self.turret_right_locations)
                self.build_queue.append(self.factory_extra_locations)
        else:
            self.build_queue.clear()
            self.build_queue.append(self.factory_base_locations)
            self.build_queue.append(self.factory_extra_locations)
            game_state.attempt_upgrade(self.factory_extra_locations["loc"])

        for struct in self.build_queue:
            game_state.attempt_spawn(struct["type"], struct["loc"])
            game_state.attempt_upgrade(struct["loc"])

        #game_state.attempt_upgrade(self.turret_base_locations["loc"])
        game_state.attempt_upgrade(self.factory_base_locations["loc"])

    def find_intercept_path(self, instance):
        # 5,8: 29 spaces
        # 6, 7: 27 spaces
        # 14, 0: 24 spaces 12
        # 15, 1: 22 spaces 11
        # 16, 2: 20 spaces 10
        # 17, 3: 18 spaces
        # 18, 4: 16 spaces
        # 19, 5: 14 spaces
        # 20, 6: 12 spaces
        # 21, 7: 10 spaces
        # 22, 8: 8 spaces
        # 23, 9: 6 spaces 
        if instance[0] > 118:
            return [5, 8]
        elif instance[0] > 108:
            return [6, 7]
        elif instance[0] > 96:
            return [14, 0]
        else:
            return [26 - int(instance[0]/8), 12 - int(instance[0]/8)]

    def scout_attack(self, game_state, num):
        if num == 0:
            return
        loc, damage = self.least_damage_spawn_location(game_state, [[13, 0], [13, 1], [11, 2], [12, 1], [26, 12]])
        if damage == 0:
            game_state.attempt_spawn(SCOUT, [loc], game_state.number_affordable(SCOUT))
        if damage/(num * 15) < 0.9:
            game_state.attempt_spawn(SCOUT, [loc], num)


    def demolisher_attack(self, game_state, num):
        loc, damage = self.least_damage_spawn_location(game_state, [[26, 12]])
        if damage == 0:
            game_state.attempt_spawn(DEMOLISHER, [loc], num)
            return
        if self.damage_dealt(game_state, loc, DEMOLISHER, num) / damage > 3:
            game_state.attempt_spawn(DEMOLISHER, [loc], num)

    def stall_with_interceptors(self, game_state, cost):
        """
        Send out interceptors at random locations to defend our base from enemy moving units.
        """            

        deploy_locations = [[2, 11], [25, 11], [4, 9], [23, 9], [6, 7], [21, 7], [8, 5], [19, 5], [10, 3], [17, 3], [12, 1], [15, 1]]
        spent = 0

        # While we have remaining MP to spend lets send out interceptors randomly.
        while game_state.get_resource(MP) >= game_state.type_cost(INTERCEPTOR)[MP] and len(deploy_locations) > 0 and cost > spent:
            if len(self.recurring_line_crossing.keys()) == 0:
                gamelib.debug_write("Empty crossings list")
                game_state.attempt_spawn(INTERCEPTOR, random.choice(deploy_locations))
                spent += 1
                continue
            ins = random.choices(list(self.recurring_line_crossing.keys()), list(self.recurring_line_crossing.values()))
            game_state.attempt_spawn(INTERCEPTOR, self.find_intercept_path(ins[0]))
            spent += 1
            """
            We don't have to remove the location since multiple mobile 
            units can occupy the same space.
            """

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
            if path == None:
                # gamelib.debug_write(str(location))
                continue
            for path_location in path:
                # Get number of enemy turrets that can attack each location and multiply by turret damage
                damage += len(game_state.get_attackers(path_location, 0)) * gamelib.GameUnit(TURRET, game_state.config).damage_i
            damages.append(damage)
        
        # Now just return the location that takes the least damage
        return location_options[damages.index(min(damages))], min(damages)

    def damage_dealt(self, game_state, loc, unit, num):
        path = game_state.find_path_to_edge(loc)
        for unit_info in game_state.config["unitInformation"]:
            if unit_info["shorthand"] == unit:
                damage = unit_info["attackDamageTower"]
                health = unit_info["startHealth"]
                rng = unit_info["attackRange"]

        total_damage = 0
        for location in path:
            for attack_loc in game_state.game_map.get_locations_in_range(location, rng):
                for unit in game_state.game_map[attack_loc]:
                    if unit.player_index == 1:
                        total_damage += damage*num
            
        return total_damage

    def on_action_frame(self, turn_string):
        """
        This is the action frame of the game. This function could be called 
        hundreds of times per turn and could slow the algo down so avoid putting slow code here.
        Processing the action frames is complicated so we only suggest it if you have time and experience.
        Full doc on format of a game frame at: https://docs.c1games.com/json-docs.html
        """
        # Let's record at what position we get scored on
        state = json.loads(turn_string)
        for movement in state["events"]["move"]:
            if movement[5] == 2 and movement[0][1] == 14 and movement[0][0] > 20 and movement[0][0] < 28:
                self.enemy_unit_movement.append([self.frame_count, movement])
        self.frame_count += 1

        events = state["events"]
        breaches = events["breach"]
        for breach in breaches:
            location = breach[0]
            unit_owner_self = True if breach[4] == 1 else False
            # When parsing the frame data directly, 
            # 1 is integer for yourself, 2 is opponent (StarterKit code uses 0, 1 as player_index instead)
            if not unit_owner_self:
                gamelib.debug_write("Got scored on at: {}".format(location))
                location_coordinates = (location[0], location[1])
                if location_coordinates in self.scored_on_locations:
                    self.scored_on_locations[location_coordinates] += 1
                else:
                    self.scored_on_locations[location_coordinates] = 1
                gamelib.debug_write("All locations: {}".format(self.scored_on_locations))

if __name__ == "__main__":
    algo = AlgoStrategy()
    algo.start()

