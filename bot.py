import urllib
import json
import time
from boat import Boat
import re

posre = re.compile('!\d')

IDLE = 0
WAITING_NEW_CONFIRM = 1
WAITING_REPLACE_CONFIRM = 2

class Bot(object):
    def __init__(self, token):
        self.__token = token
        self.__last_received_update = None
        self.__boat = None
        self.__status = IDLE
        self.__cache_pos = 0
        self.__cache_replace = 0


    def __run_method(self, method, params=None):
        p = None
        if params is not None:
            p = urllib.urlencode(params)
        return json.loads(urllib.urlopen('https://api.telegram.org/bot%s/%s' % (self.__token,
            method),p).read())

    def __get_updates(self,offset=None):
        params = None
        if offset is None:
            if self.__last_received_update is not None:
                offset = self.__last_received_update + 1
        if offset is not None:
            params = {'offset': offset}
        updates = self.__run_method('getUpdates',params)
        if len(updates['result']) > 0:
            self.__last_received_update = updates['result'][-1]['update_id']
        return updates['result']

    def send_message(self, chat_id, text):
        params = {'chat_id': chat_id, 'text': text}
        updates = self.__run_method('sendMessage',params)

    def __handle_message(self, msg):
        sender = msg['from']
        text = msg['text'].strip()
        chat_id = msg['chat']['id']
        splitted = text.split(' ',2)
        cmd = splitted[0]
        params = None
        if len(splitted) > 1:
            params = splitted[1].strip()
        if cmd == '!new' or cmd == '!yes' and self.__status == WAITING_NEW_CONFIRM:
            if self.__boat and cmd == '!new':
                self.send_message(chat_id, 'Are you sure you want to erase the last practice?')
                self.__status = WAITING_NEW_CONFIRM
                return

            self.__status = IDLE
            print 'New boat!'
            if params == None:
                params = 8
            self.__boat = Boat(int(params))
            self.send_message(chat_id, 'Who is coming to the next ' +
                    'practice?\nPress "!" and the number you would like ' +
                    'to take. For example, if you would like to sit at ' +
                    'Liron\'s place with a view to Loch-Blecher, send the ' +
                    'message "!1"')
        elif posre.match(cmd) or cmd == '!yes' and self.__status == WAITING_REPLACE_CONFIRM:
            if self.__boat is None:
                return
            pos = 0
            print 'New rower!'
            name = '%s %s' % (sender['first_name'], sender['last_name'])
            if params is not None:
                name = params
            if cmd == '!yes':
                pos = self.__cache_pos
                name = self.__cache_name
            else:
                pos = int(cmd[1])
            if self.__boat.rowers[pos-1] is not None and cmd != '!yes':
                self.send_message(chat_id, 'This spot is already taken by ' +
                        '%s, are you sure you want to replace it?' %
                        self.__boat.rowers[pos-1])
                self.__status = WAITING_REPLACE_CONFIRM
                self.__cache_pos = pos
                self.__cache_name = name
                return

            self.__status = IDLE
            self.__boat.add_rower(pos, name)
            if len(self.__boat.get_missing()) == 0:
                #self.send_message(chat_id, u'\U0001F3BA\U0001F3BA\U0001F3BA')
                rowers = self.__boat.rowers
                ret = ''
                i = 1
                for x in rowers:
                    if x is None:
                        x = "???"
                    ret = '\n%d. %s' % (i,x) + ret
                    i += 1
                self.send_message(chat_id,
                        r'We have a boat!' + ret)


        elif cmd == '!missing':
            self.__status = IDLE
            if self.__boat == None:
                return
            missing = ', '.join([str(x) for x in self.__boat.get_missing()])
            self.send_message(chat_id, 'We are still missing %s!' % missing)
        elif cmd == '!status':
            self.__status = IDLE
            if self.__boat == None:
                self.send_message(chat_id, 'No active session')
            else:
                rowers = self.__boat.rowers
                ret = ''
                i = 1
                for x in rowers:
                    if x is None:
                        x = "???"
                    ret = '\n%d. %s' % (i,x) + ret
                    i+=1
                self.send_message(chat_id,'Current status:' + ret)

    def message_loop(self):
        while True:
            updates = self.__get_updates()
            for x in updates:
                try:
                    msg = x['message']
                    self.__handle_message(msg)
                except:
                    pass
            time.sleep(1)

b = Bot('TOKEN!!!!')
b.message_loop()
