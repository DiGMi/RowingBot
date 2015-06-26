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
        self.__boat = {} 
        self.__status = {}
        self.__cache_pos = {}
        self.__cache_name = {}
        self.__cache_size = {}


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
        splitted = text.split(' ',1)
        cmd = splitted[0]
        params = None
        boat = None
        if chat_id in self.__boat:
            boat = self.__boat[chat_id]
        if len(splitted) > 1:
            params = splitted[1].strip()
        if cmd == '!new' or cmd == '!yes' and chat_id in self.__status and self.__status[chat_id] == WAITING_NEW_CONFIRM:
            if boat and cmd == '!new':
                self.send_message(chat_id, 'Are you sure you want to erase the last practice?')
                self.__status[chat_id] = WAITING_NEW_CONFIRM
                self.__cache_size[chat_id] = params
                return

            self.__status[chat_id] = IDLE
            print 'New boat!'
            if params is None:
                params = 8
                if chat_id in self.__cache_size:
                    params = self.__cache_size[chat_id]
                    if params is None:
                        params = 8
            self.__boat[chat_id] = Boat(int(params))
            self.send_message(chat_id, 'Who is coming to the next ' +
                    'practice?\nPress "!" and the number you would like ' +
                    'to take. For example, if you would like to sit at ' +
                    'Liron\'s place with a view to Loch-Blecher, send the ' +
                    'message "!1"')
        elif posre.match(cmd) or cmd == '!yes' and chat_id in self.__status and self.__status[chat_id] == WAITING_REPLACE_CONFIRM:
            if boat is None:
                return
            pos = 0
            print 'New rower!'
            name = '%s %s' % (sender['first_name'], sender['last_name'])
            if params is not None:
                name = params
            if cmd == '!yes':
                pos = self.__cache_pos[chat_id]
                name = self.__cache_name[chat_id]
            else:
                pos = int(cmd[1])
            if boat.rowers[pos-1] is not None and cmd != '!yes':
                self.send_message(chat_id, 'This spot is already taken by ' +
                        '%s, are you sure you want to replace it?' %
                        boat.rowers[pos-1])
                self.__status[chat_id] = WAITING_REPLACE_CONFIRM
                self.__cache_pos[chat_id] = pos
                self.__cache_name[chat_id] = name
                return

            self.__status[chat_id] = IDLE
            print pos,name
            boat.add_rower(pos, name)
            if len(boat.get_missing()) == 0:
                #self.send_message(chat_id, u'\U0001F3BA\U0001F3BA\U0001F3BA')
                rowers = boat.rowers
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
            self.__status[chat_id] = IDLE
            if boat is None:
                return
            missing = ', '.join([str(x) for x in boat.get_missing()])
            self.send_message(chat_id, 'We are still missing %s!' % missing)
        elif cmd == '!status':
            self.__status[chat_id] = IDLE
            if boat is None:
                self.send_message(chat_id, 'No active session')
            else:
                rowers = boat.rowers
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

b = Bot('Toke!!!')
b.message_loop()
