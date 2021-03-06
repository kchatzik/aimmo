from pprint import pformat
import abc

import json
import logging

logging.basicConfig()
LOGGER = logging.getLogger(__name__)
LOGGER.setLevel(logging.DEBUG)

class BaseSnapshotProcessor():
    __metaclass__ = abc.ABCMeta

    @abc.abstractmethod
    def receive_snapshot(self, information):
        pass

class SnapshotProcessor(BaseSnapshotProcessor):
    def __init__(self, binder, player_id = 1):
        self.binder = binder
        self.world_states = []
        self.player_id = player_id
        self.player_added = False

    def check_player_moved_at_most_one_space(self, last_pos, curr_pos):
        if last_pos is None:
            return
        if curr_pos is None:
            return
        x_diff = last_pos['x'] - curr_pos['x']
        y_diff = last_pos['y'] - curr_pos['y']

        x_move = x_diff >= -1 and x_diff <= 1 and y_diff == 0
        y_move = y_diff >= -1 and y_diff <= 1 and x_diff == 0

        LOGGER.info("Checking player movement...")
        LOGGER.info(str((last_pos['x'], last_pos['y'])) + " -> " + str((curr_pos['x'], curr_pos['y'])))
        if x_diff == 0 and y_diff == 0:
            LOGGER.info("No movement > OK")
        elif x_move:
            LOGGER.info("Movement on x axes > OK")
        elif y_move:
            LOGGER.info("Movement on y axes > OK")
        else:
            LOGGER.error("To many moves > FAIL")
        self.binder.assertTrue(x_move or y_move)

    def get_player(self, world_state):
        players = world_state['players']['create'] + world_state['players']['update']
        return [player for player in players if player['id'] == self.player_id][0]

    def check_changes_world_state(self):
        last_world_state = self.world_states[-2]
        world_state = self.world_states[-1]
        self.world_states.append(world_state)

        try:
            self.get_player(last_world_state)
        except IndexError:
            return

        self.player_added = True
        self.check_player_moved_at_most_one_space(
            self.get_player(last_world_state),
            self.get_player(world_state)
        )

    def check_only_feature_creations_happen(self, world_state):
        LOGGER.info("Receiving initial world state...")
        LOGGER.info(pformat(world_state))
        for key, feature in world_state['map_features'].iteritems():
            if 'update' in feature.keys():
                self.binder.assertEqual(len(feature['update']), 0)

    def check_first_world_state(self):
        world_state = self.world_states[-1]

        LOGGER.info("Checking only feature creations happen...")
        self.check_only_feature_creations_happen(world_state)

    def receive_snapshot(self, world_state_string):
        world_state = json.loads(world_state_string)

        self.world_states.append(world_state)
        if len(self.world_states) == 1:
            self.check_first_world_state()
        else:
            self.check_changes_world_state()

    def check_player_added(self):
        self.binder.assertTrue(self.player_added)
