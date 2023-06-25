# импорты
import vk_api
from vk_api.longpoll import VkLongPoll, VkEventType
from vk_api.utils import get_random_id

from config import community_token, access_token
from core import VkTools

from datetime import datetime 
from dateutil.relativedelta import relativedelta
from data_store import Viewed
import json

class BotInterface():
    #Вопросы, которые бот задает, если недостаточно информации о пользователе
    param_questions = {
        'name': 'Как вас зовут?',
        'bdate': 'Сколько Вам лет?',
        'home_town': 'Из какого Вы города?',
        'sex': 'Каков Ваш пол?',
        'relation': 'Вы состоите в отношениях?'
        }

    def __init__(self,community_token, access_token):
        self.interface = vk_api.VkApi(token=community_token)
        self.api = VkTools(access_token)
        self.params = None
        #Недостающий для поиска параметр пользователя
        self.missing_param = None
        #Найденные пользователи 
        self.users = None
        #Экземпляр класса для работы с БД
        self.viewed = Viewed()

    #рекурсивная процедура проверки достаточности параметров пользовател
    def validate_params(self,user_answer=None):
        if self.missing_param is None:
            for param_name, param_value in self.params.items():
                if param_value is None:
                    #если встречаем пустой параметр то запоминаем его и отправляем вопрос пользователю
                    self.missing_param = param_name
                    self.message_send(int(self.params['id']), self.param_questions[self.missing_param])
                    return
            self.missing_param = None
        #если же есть недостающие параметры пользователя
        else:
             if self.missing_param == 'bdate':
                for s in user_answer.split():
                    if s.isdigit():
                        age = int(s)
                        bdate = datetime.now() - relativedelta(years=age)
                        self.params[self.missing_param] = bdate.strftime("%d.%m.%Y")
                        self.missing_param = None
                        break
             elif self.missing_param == 'sex':
                if(user_answer.find('м')):
                    self.params[self.missing_param] = 1
                else:
                    self.params[self.missing_param] = 2
                self.missing_param = None
             else:
                 self.params[self.missing_param] = user_answer
                 self.missing_param = None
             #повторная проверка
             self.validate_params(self)

    def execute_command(self,uid, command):
         if command == 'поиск':
            self.users = self.api.search_users(self.params)
            self.execute_command(uid,"еще")
         elif command == 'еще':
             if (self.users is not None and len(self.users)>0):
                user = self.users.pop()
                while(self.viewed.profile_exists(uid, int(user['id'])) == True):
                    user = self.users.pop()
                photos_user = self.api.get_photos(user['id'])
                attachment = list()
                for num, photo in enumerate(photos_user):                    
                    attachment.append(f'photo{photo["owner_id"]}_{photo["id"]}')
                    if num == 2:
                        break
                self.message_send(uid,
                                      f'Встречайте {user["name"]}',
                                      attachment=','.join(attachment)
                                      ) 
         elif command == 'пока':
            self.params = None
            self.missing_param = None
            self.message_send(uid, 'пока')
         else:
             if self.missing_param is None:
                 self.message_send(uid, 'для поиска партнера наберите команду поиск')
             else:
                self.validate_params(command)



    def message_send(self, user_id, message, attachment=None):
        self.interface.method('messages.send',
                                {'user_id': user_id,
                                'message': message,
                                'attachment': attachment,
                                'random_id': get_random_id()
                                }
                                )
        
    def event_handler(self):
        longpoll = VkLongPoll(self.interface)
  
        for event in longpoll.listen():
            if event.type == VkEventType.MESSAGE_NEW and event.to_me:
                command = event.text.lower()
                
                #Если пользователь новый, то обновить информацию о нем
                if(self.params is None or int(self.params['id'])!=event.user_id):
                    self.params = self.api.get_profile_info(event.user_id)
                    #Начать проверку достаточности данных пользователя
                    self.validate_params()
                #Если пользователь нам уже известен
                else:
                    #Если есть незаполненные поля в профиле пользователя
                    if(self.missing_param is not None):
                        #Считаем его сообщение ответом на вопрос
                        self.validate_params(command)
                        #если его ответ устранил недостаточность данных
                        if(self.missing_param is None):
                            #выполняем поиск профилей для него
                            self.execute_command(event.user_id,'поиск')
                        #иначе продолжаем уточнять данные
                        else:
                            self.validate_params()
                    else:
                        self.execute_command(event.user_id,command)
                            

                    
                

                    
                


if __name__ == '__main__':
    bot = BotInterface(community_token, access_token)
    bot.event_handler()

            

