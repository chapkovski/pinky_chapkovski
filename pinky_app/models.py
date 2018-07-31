from otree.api import (
    models, widgets, BaseConstants, BaseSubsession, BaseGroup, BasePlayer,
    Currency as c, currency_range
)

from django.db import models as djmodels
import random
from django.db.models.signals import post_save
import string
from .fields import ListField

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
                     'moderate': .75,
                     'hard': 1}
    # For RET block
    task_len = 8
    num_digits = 10
    num_letters = 10
    practice_task_time_seconds = 60  # how long does the Practice task lasts in seconds
    task_time_seconds = 60  # how long does the LIVE task lasts in seconds

    # END OF  For RET block

    pay_per_unit = c(1)


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
    target = models.IntegerField(doc='target for this group')
    target_met = models.BooleanField(choices=((False, 'Not met'), (True, 'Met')))
    sum_live_correct = models.IntegerField(doc='total amount of correctly solved tasks in Work Session')

    def set_payoffs(self):
        # if contract is piece-rated one formula
        #  if contract is budget linear another formula for calculationg payoffs

        self.sum_live_correct = sum([p.tasks_solved for p in self.get_players()])
        self.target_met = self.sum_live_correct >= self.target
        for p in self.get_players():
            p.payoff = Constants.pay_per_unit * (p.tasks_solved + self.sum_live_correct)
            if self.contract_type == 'budget-linear':
                p.payoff *= self.target_met

    def set_targets(self):
        # todo: should be redone if we do another mechansim (based on task type) than a page name.
        # TODO: SHOULD BE DONE sooner or later!
        sum_practice_correct = sum([p.practice_tasks_solved for p in self.get_players()])
        self.target = int(Constants.target_levels[self.target_level] * sum_practice_correct)


class Player(BasePlayer):
    dump_practice_tasks = models.LongStringField()
    dump_live_tasks = models.LongStringField()
    practice_tasks_solved = models.IntegerField(initial=0,
                                                doc='tasks solved  during the Practice')

    tasks_solved = models.IntegerField(initial=0,
                                       doc='points earned during the RET')

    def get_answered_tasks(self):
        # WARNING: the way it is done now it will return correct number of tasks only if method is called
        # by player from the workpage (because otherwise partcipant moves his position in index)
        # TODO: redo this BS so it won't be based on the page name?
        curpage = self.participant._index_in_pages
        return self.tasks.filter(page_index=curpage, answer__isnull=False)

    @property
    def num_answered(self):
        # WARNING: the way it is done now it will return correct number of tasks only if method is called
        # by player from the workpage (because otherwise partcipant moves his position in index)
        curpage = self.participant._index_in_pages
        return self.get_answered_tasks().count()

    @property
    def num_correct(self):
        return self.get_answered_tasks().filter(is_correct=True).count()

    @property
    def num_incorrect(self):
        return self.get_answered_tasks().filter(is_correct=False).count()

    @property
    def totnum_tasks(self):
        return self.get_answered_tasks().count()

    # ######## END OF TEMPBLOCK ########

    def get_unfinished_tasks(self):
        curpage = self.participant._index_in_pages
        return self.tasks.filter(answer__isnull=True, page_index=curpage)


class Task(djmodels.Model):
    player = djmodels.ForeignKey(to=Player, related_name='tasks')
    question = ListField()
    correct_answer = ListField()
    digits = ListField()
    letters = ListField()
    answer = models.StringField(null=True)
    page_index = models.IntegerField()
    page_name = models.StringField(doc='page name of task submission', null=True)
    is_correct = models.BooleanField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # todo: the following methods can and should be done through currying
    # https://stackoverflow.com/questions/5730211/how-does-get-field-display-in-django-work
    def get_str(self, field):
        return ''.join(getattr(self, field))

    def get_digits(self):
        return self.get_str('digits')

    def get_letters(self):
        return self.get_str('letters')

    def get_question(self):
        return self.get_str('question')

    def get_correct_answer(self):
        return self.get_str('correct_answer')

    def get_body(self):
        return {
            'question': self.question,
            'digits': self.digits,
            'letters': self.letters,
        }

    def decoding_dict(self):
        keys = self.digits
        values = self.letters
        dictionary = dict(zip(keys, values))
        return dictionary

    def get_decoded(self, to_decode):
        decdict = self.decoding_dict()
        return [decdict[i] for i in to_decode]

    def as_dict(self):
        # TODO: clean the mess with the body
        # TODO: remove correct answer when go into production
        return {
            'correct_answer': self.correct_answer,
            'body': self.get_body()
        }

    @classmethod
    def post_create(cls, sender, instance, created, *args, **kwargs):
        if not created:
            return
        instance.page_index = instance.player.participant._index_in_pages
        instance.page_name = instance.player.participant._url_i_should_be_on().strip().split('/')[-3]
        digs = list(string.digits)
        random.shuffle(digs)
        instance.digits = digs
        lts = random.sample(string.ascii_lowercase, k=Constants.num_letters)
        instance.letters = lts
        instance.question = random.choices(string.digits, k=Constants.task_len)
        instance.correct_answer = instance.get_decoded(instance.question)
        instance.save()


post_save.connect(Task.post_create, sender=Task)
