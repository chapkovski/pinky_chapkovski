from otree.api import Currency as c, currency_range
from ._builtin import Page, WaitPage
from .models import Constants
import json
from datetime import date, datetime


# Some functions to deal with datetime serialization

def json_serial(obj):
    """JSON serializer for objects not serializable by default json code"""
    if isinstance(obj, (datetime, date)):
        return obj.isoformat()
    raise TypeError("Type %s not serializable" % type(obj))


class RETPage(Page):
    template_name = 'pinky_app/WorkPage.html'
    _allow_custom_attributes = True

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_index'] = self._index_in_pages
        return context

    def vars_for_template(self):
        unanswered_tasks = self.player.get_unfinished_tasks()
        if unanswered_tasks.exists():
            task = unanswered_tasks.first()
        else:
            task = self.player.tasks.create()
        t = zip(task.digits, task.letters)
        return {'num_digits': range(Constants.num_digits),
                'task': t,
                'question': ''.join(task.question)}


class Intro(Page):
    ...


class BeforeTrainingWP(WaitPage):
    ...


class Training(RETPage):
    title = 'Decoding task: training session'
    timeout_seconds = Constants.practice_task_time_seconds

    def before_next_page(self):
        self.player.practice_tasks_solved = self.player.num_correct
        self.player.dump_practice_tasks = json.dumps(list(self.player.get_answered_tasks().values()),
                                                     default=json_serial)


class BeforeWorkWP(WaitPage):
    def after_all_players_arrive(self):
        self.group.set_targets()
class AnnouncingTarget(Page):
    ...

class Work(RETPage):
    title = 'Decoding task: work session'
    timeout_seconds = Constants.task_time_seconds

    def before_next_page(self):
        self.player.tasks_solved = self.player.num_correct
        self.player.dump_live_tasks = json.dumps(list(self.player.get_answered_tasks().values()),
                                                 default=json_serial)


class BeforeResultsWP(WaitPage):
    def after_all_players_arrive(self):
        self.group.set_payoffs()


class Results(Page):
    ...


page_sequence = [
    # Intro,
    # BeforeTrainingWP,
    Training,
    BeforeWorkWP,
    AnnouncingTarget,
    Work,
    BeforeResultsWP,
    Results,
]
