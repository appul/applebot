import html
import re
import time
import urllib.parse
from collections import UserDict
from typing import Dict
from typing import Union

import aiohttp
import discord
from pyquery import PyQuery

from applebot.botmodule import BotModule
from applebot.utils import table_align

PROFILE_URL = 'http://{region}-bns.ncsoft.com/ingame/bs/character/profile?c={name}'

LETTER_PATTERN = re.compile(r'[a-z]', re.IGNORECASE)

OUTPUT_FORMAT = 'Player: **{p.name}** <{p.clan}> | Level: {p.level}, HM: {p.mastery}\n```{stats}```'
PROFILE_FORMAT = [
    ['Attack Power', '{stats[Attack Power]}', '|', 'Health', '{stats[HP]}'],
    ['Critical Hit', '{stats[Critical Hit]} ({stats[Critical Hit][Critical Rate]}%)', '|', 'Defense', '{stats[Defense]} ({stats[Defense][Damage Reduction]}%)'],
    ['Critical Damage', '{stats[Critical Damage]} ({stats[Critical Damage][Increase Damage]}%)', '|', 'Evasion', '{stats[Evasion]} ({stats[Evasion][Evasion Rate]}%)'],
    ['Accuracy', '{stats[Accuracy]} ({stats[Accuracy][Hit Rate]}%)', '|', 'Block', '{stats[Block]} ({stats[Block][Block Rate]}%)']
]


class BnsProfileModule(BotModule):
    def __init__(self):
        super().__init__()
        self.session = BnsClientSession()  # type: BnsClientSession
        self._last_command = 0

    @BotModule.command('profile')
    async def on_profile_command(self, message):
        """`!profile <player name>` | Retrieves a player profile"""
        assert isinstance(message, discord.Message)
        if time.time() - self._last_command < 5: return
        self._last_command = time.time()
        player = message.content[9:]
        profile = await self.session.get_profile(player)
        stats = '\n'.join([' '.join(r) for r in (table_align(profile.format(PROFILE_FORMAT)))])
        output = OUTPUT_FORMAT.format(p=profile, stats=stats)
        await self.client.send_message(message.channel, output)


class BnsClientSession(object):
    def __init__(self, session=None):
        self.session = session or aiohttp.ClientSession()  # type: aiohttp.ClientSession

    async def get_profile(self, name, region='eu'):
        request = BnsProfileRequest(name=name, region=region, session=self.session)
        profile = await request.send()
        return profile


class BnsProfileRequest(object):
    def __init__(self, name, region='eu', session=None):
        self._session = session or aiohttp.ClientSession()  # type: aiohttp.ClientSession
        self.profile = BnsProfile()  # type: BnsProfile
        self.profile_name = name  # type: str
        self.region = region  # type: str
        self.response = None  # type: aiohttp.Response

    async def send(self):
        async with self._session.get(self._request_url) as response:
            self.profile.parse(await response.text())
            return self.profile

    @property
    def _request_url(self):
        return PROFILE_URL.format(name=urllib.parse.quote_plus(self.profile_name), region=self.region)


class BnsProfile(object):
    def __init__(self):
        self._body = None  # type: PyQuery
        self.name = None  # type: str
        self.clan = None  # type: str
        self.job = None  # type: str
        self.level = None  # type: int
        self.mastery = None  # type: int
        self.server = None  # type: str
        self.faction = None  # type: str
        self.stats = {}  # type: Dict[str, BnsProfileStat]

    def parse(self, response):
        self._body = PyQuery(response)
        self.name = self._body('span.name').text().strip('[]')
        self.clan = self._body('li.guild').text()

        desc = self._body('dd.desc')('li')
        self.job = desc.eq(0).text()
        self.server = desc.eq(2).text()
        self.level = int(re.findall(r'\d+', desc.eq(1).text())[0])
        self.mastery = int(re.findall(r'\d+', self._body('span.masteryLv').text())[0])
        self.faction = html.unescape(desc.eq(3).text())

        for stat_ele in self._body('dt.stat-title').items():
            stat = BnsProfileStat.parse(stat_ele)
            self.stats[stat.name] = stat

    def format(self, template):
        if not isinstance(template, (list, tuple)):
            return template.format(**self.__dict__)
        return [self.format(t) for t in template]


class BnsProfileStat(UserDict):
    def __init__(self, name, value, substats=None):
        super().__init__(substats)
        self.name = name  # type: str
        self.text = value  # type: str
        self.value = self.parse_value(value)  # type: Union[str, int, float]

    def __str__(self):
        return self.text

    @staticmethod
    def parse(stat_ele):
        assert isinstance(stat_ele, PyQuery)
        name = stat_ele.find('span.title').text()
        value = stat_ele.find('span.stat-point').text()
        substats = {}

        for substat_ele in stat_ele.next_all('dd.stat-description').eq(0).find('li').items():
            stat = BnsProfileStat.parse(substat_ele)
            substats[stat.name] = stat

        return BnsProfileStat(name, value, substats)

    @staticmethod
    def parse_value(value):
        if not isinstance(value, str):
            return value
        if LETTER_PATTERN.match(value):
            return value
        if '%' in value:
            return float(value.strip('%')) / 100
        return int(value)
