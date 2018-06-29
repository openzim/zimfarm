from sshtunnel import SSHTunnelForwarder
from pymongo import MongoClient
from pycountry import languages

# with SSHTunnelForwarder('farm.openzim.org',
#                         ssh_username='chris',
#                         ssh_pkey='~/.ssh/id_rsa',
#                         remote_bind_address=('127.0.0.1', 27017)) as tunnel:
#
#     client = MongoClient('127.0.0.1', tunnel.local_bind_port)
#     collection = client['Zimfarm']['schedules']
#
#     documents = [document for document in collection.find({})]
#     for document in documents:
#         language = languages.lookup(document['language'])
#
#         collection.update_one({'_id': document['_id']}, {'$set': {
#             'language': language.alpha_3
#         }})


print({language.alpha_3: language.name for language in list(languages)})