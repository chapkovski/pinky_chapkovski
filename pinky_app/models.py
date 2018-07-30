from otree.api import (
    models, widgets, BaseConstants, BaseSubsession, BaseGroup, BasePlayer,
    Currency as c, currency_range
)

author = 'Philipp Chapkovski, chapkovski@gmail.com'

doc = """
RET - contract and PGG, R. Pinky, Ph. Chapkovski
"""

wrong_contract_err_msg = 'Something wrong with contract name'
wrong_target_err_msg = 'smth wrong with target level name'


class Constants(BaseConstants):
    name_in_url = 'pinky_app'
    players_per_group = None
    num_rounds = 1
    contract_types = ['piece-rate', 'budget-linear']
    target_levels = {'easy': .5,
                     'medium': .75,
                     'hard': 1}


class Subsession(BaseSubsession):
    def _check_config(self):
        assert self.session.config['contract_type'] in Constants.contract_types, wrong_contract_err_msg
        assert self.session.config['target_level'] in Constants.target_levels.keys(), wrong_target_err_msg

    def creating_session(self):
        if not self.session.config.get('random'):
            if self.round_number == 1:
                self._check_config()
            for g in self.get_groups():
                g.contract_type = self.session.config.get('contract_type')
                g.target_level = self.session.config.get('target_level')


class Group(BaseGroup):
    contract_type = models.StringField(doc='piece-rate or group-budget-linear level is used in a group')
    target_level = models.StringField(doc='how hard is the group target level (easy, medium etc..)')

    def set_payoff(self):
        ...


class Player(BasePlayer):
    pass
